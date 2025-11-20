
import json
import time
from typing import Any, Dict, List, Tuple

import concurrent.futures
from dotenv import load_dotenv
from openai import OpenAI

from Config.config import MAX_WORKERS, max_tokens, model_name, temperature
from Logs.logs import setup_logging
from Tool.Google_search import google_search
from Tool.scripty_jiaodian import search_jiaodian_news
from Tool.scripty_jiaowu_system import search_jiaowu_score
from Tool.scripty_school_card import search_school_card_text
from Tool.search_library import search_library_data
from Tool.tools_description import tools_description
from prompt.Master_prompt import master_prompt

logger = setup_logging()

load_dotenv()

client = OpenAI()

TOOL_FUNCTIONS = {
    "google_search": google_search,
    "search_jiaodian_news": search_jiaodian_news,
    "search_school_card_text": search_school_card_text,
    "search_library_data": search_library_data,
    "search_jiaowu_score": search_jiaowu_score,
}

# 调用模型
def call_openai(messages: List[Dict[str, Any]]):
    return client.chat.completions.create(
        model=model_name,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        tools=tools_description,
        tool_choice="auto",
    )


# 调用工具
def execute_tool_call(tool_call) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    执行单个工具调用，返回用于 OpenAI 对话的 tool 消息和记录摘要。
    """
    function_name = tool_call.function.name
    raw_arguments = tool_call.function.arguments or "{}"
    function_args = json.loads(raw_arguments)

    func = TOOL_FUNCTIONS.get(function_name)
    logger.info("• 调用工具: %s", function_name)
    logger.info("• 参数: %s", function_args)


    result_data = func(**function_args)
    result_payload = {
        "success": True,
        "data": result_data,
    }


    logger.info("• 结果: %s", result_payload)

    tool_message = {
        "role": "tool",
        "tool_call_id": tool_call.id,
        "content":f"{result_payload}"
    }

    return tool_message

# 消耗统计
def _log_execution_summary(
    execution_time: float,
    iterations: int,
    api_call_count: int,
    total_prompt_tokens: int,
    total_completion_tokens: int,
    total_tokens: int,
) -> None:
    logger.info("==" * 60)
    logger.info("• 执行统计报告:")
    logger.info("• 执行用时: %.2f秒", execution_time)
    logger.info("• 总迭代轮数: %s", iterations)
    logger.info("• API调用次数: %s", api_call_count)
    logger.info("• Token消耗统计:")
    logger.info("• 输入Token: %s", f"{total_prompt_tokens:,}")
    logger.info("• 输出Token: %s", f"{total_completion_tokens:,}")
    logger.info("• 总Token: %s", f"{total_tokens:,}")
    if api_call_count:
        logger.info("• 平均每次调用: %.1f tokens", total_tokens / api_call_count if total_tokens else 0)
    logger.info("==" * 60)

# 主逻辑
def run_master_agent(user_input: str, max_iterations: int = 10) -> str:
    """
    执行面向深圳技术大学场景的智能助手循环，直到获得最终回答或达到迭代上限。
    """
    start_time = time.time()
    total_prompt_tokens = 0
    total_completion_tokens = 0
    total_tokens = 0
    api_call_count = 0

    logger.info("• 用户查询: %s", user_input)
    logger.info("==" * 60)

    message = [{"role": "user", "content": f"用户问题:{user_input}"},{"role": "system", "content": master_prompt}]


    for iteration in range(1, max_iterations + 1):
        logger.info("• 第 %s 轮工具调用:", iteration)


        response = call_openai(message)

        # 打印运行日志
        api_call_count += 1
        if getattr(response, "usage", None):
            prompt_tokens = response.usage.prompt_tokens
            completion_tokens = response.usage.completion_tokens
            tokens_used = response.usage.total_tokens
            total_prompt_tokens += prompt_tokens
            total_completion_tokens += completion_tokens
            total_tokens += tokens_used
            logger.info(
                "• API调用 %s: 输入%s + 输出%s = %s tokens",
                api_call_count,
                prompt_tokens,
                completion_tokens,
                tokens_used,
            )


        conversation = {
            "role": response.choices[0].message.role,
            "content": response.choices[0].message.content,
        }
        if response.choices[0].message.tool_calls:
            conversation["tool_calls"] = response.choices[0].message.tool_calls

        # 添加消息列表
        message.append(conversation)

        tool_calls = response.choices[0].message.tool_calls or []

        if not tool_calls:
            final_content = response.choices[0].message.content or ""
            execution_time = time.time() - start_time
            _log_execution_summary(
                execution_time,
                iteration,
                api_call_count,
                total_prompt_tokens,
                total_completion_tokens,
                total_tokens,
            )
            return final_content

        logger.info("• 识别到需要调用 %s 个工具:", len(tool_calls))

        max_workers = min(MAX_WORKERS, len(tool_calls)) or 1
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_tool_call = {
                executor.submit(execute_tool_call, tool_call): tool_call
                for tool_call in tool_calls
            }
            for future in concurrent.futures.as_completed(future_to_tool_call):
                tool_message = future.result()
                message.append(tool_message)


    logger.info("• 达到最大迭代次数 (%s)，请求最终回答。", max_iterations)
    message.append({"role": "user", "content": "请基于以上工具调用结果，为用户提供准确、完整的回答。"})

    final_response = call_openai(message)

    api_call_count += 1
    if getattr(final_response, "usage", None):
        prompt_tokens = final_response.usage.prompt_tokens
        completion_tokens = final_response.usage.completion_tokens
        tokens_used = final_response.usage.total_tokens
        total_prompt_tokens += prompt_tokens
        total_completion_tokens += completion_tokens
        total_tokens += tokens_used
        logger.info(
            "• 最终回答API调用: 输入%s + 输出%s = %s tokens",
            prompt_tokens,
            completion_tokens,
            tokens_used,
        )

    execution_time = time.time() - start_time
    _log_execution_summary(
        execution_time,
        max_iterations,
        api_call_count,
        total_prompt_tokens,
        total_completion_tokens,
        total_tokens,
    )

    return final_response.choices[0].message.content or ""


def main():
    """主函数 - 测试循环工具调用的校园助手"""

    index = 1
    while   True:
        query = input("输入问题：")
        print(f"• 正在测试 {index}: {query}")
        logger.info("• 正在测试 %s: %s", index, query)
        result = run_master_agent(query, max_iterations=8)
        print(f"• 最终结果:\n{result}")
        logger.info("• 最终结果:\n%s", result)
        logger.info("==" * 60)
        index += 1


if __name__ == "__main__":
    main()

