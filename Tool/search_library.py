import requests
import json
from urllib.parse import quote
from typing import Dict, Any, List

# 预设的请求头
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*'
}


def search_library_data(keyword: str) -> Dict[str, Any]:
    """
    根据关键词获取图书馆系统的自动补全建议和主题推荐数据。
    """

    # 1. 对关键词进行 URL 编码
    encoded_keyword = quote(keyword)

    # 2. 构造 API 接口 URL
    suggest_url = f"https://lib-opac.sztu.edu.cn/meta-local/opac/search/_suggest?fieldName=all&query={encoded_keyword}&size=7"
    recommend_url = f"https://lib-opac.sztu.edu.cn/meta-local/opac/commend/subject_loan?subject={encoded_keyword}&num=6"

    api_endpoints = {
        "suggest": suggest_url,
        "recommend": recommend_url
    }

    results: Dict[str, Any] = {
        "suggest_data": None,  # 关键词自动补全结果列表
        "recommend_data": None  # 主题推荐结果列表
    }

    print(f"--- 开始查询关键词: {keyword} ---")

    # 3. 循环执行请求
    for api_type, url in api_endpoints.items():
        try:
            print(f"正在请求 {api_type} 接口...")
            response = requests.get(url, headers=HEADERS, timeout=10)
            response.raise_for_status()  # 检查 HTTP 状态码

            data = response.json()

            # 提取数据部分并存储到结果字典中
            extracted_data = data.get('data', [])

            if api_type == "suggest":
                results["suggest_data"] = extracted_data
                print(f"  > 成功获取 {len(extracted_data)} 条自动补全建议。")
            elif api_type == "recommend":
                results["recommend_data"] = extracted_data
                print(f"  > 成功获取 {len(extracted_data)} 条主题推荐结果。")

        except requests.exceptions.Timeout:
            print(f"  ❌ {api_type.upper()} 请求超时。")
        except requests.exceptions.RequestException as e:
            print(f"  ❌ {api_type.upper()} 请求失败: 网络或 HTTP 错误: {e}")
        except json.JSONDecodeError:
            print(f"  ❌ {api_type.upper()} 响应不是有效的 JSON 格式。")
        except Exception as e:
            print(f"  ❌ {api_type.upper()} 发生未知错误: {e}")

    print("--- 查询完成 ---\n")
    return results


# --- 示例调用 ---
if __name__ == "__main__":
    TEST_KEYWORD = "人工智能"

    # 调用封装好的函数
    all_results = search_library_data(TEST_KEYWORD)

    # 打印返回结果的结构
    print(all_results)
