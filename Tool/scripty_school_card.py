import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os
import re
import openai
import numpy as np
from typing import List, Dict, Optional
from dotenv import load_dotenv  # 导入 dotenv 库

load_dotenv()


# --- 爬虫脚本主函数 ---
def run_sztu_news_spider():
    """
    爬取深圳技术大学 (sztu.edu.cn) '校园一卡通' 板块的文章内容。
    将文章详情保存为单独的 .txt 文件，并生成一个标题列表文件。
    该函数无任何入参，直接调用即可触发整个爬虫流程。
    """

    # --- 1. 配置常量 (集中管理) ---
    BASE_URL = "https://it.sztu.edu.cn/"
    # 目标列表页：信息服务/校园一卡通
    TARGET_URL = urljoin(BASE_URL, "xxfw1/xyykt.htm")
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36 Edg/141.0.0.0'
    }
    OUTPUT_DIR = "../data/text_校园一卡通"
    TITLE_LIST_FILE = "text_title_list.txt"

    print(f"✅ 目标URL: {TARGET_URL}")
    print("-" * 50)

    # --- 2. 工具函数定义 ---

    def fetch_list_page(url, headers):
        """请求列表页 HTML 内容，处理网络异常。"""
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            response.encoding = 'utf-8'
            print("💡 成功获取列表页内容.")
            return response.text
        except requests.RequestException as e:
            print(f"❌ 爬取列表页失败: {e}")
            return None

    def parse_list_page(html_content, base_url):
        """从列表页提取文章链接 (href, title 属性) 和卡片显示的标题/日期。"""
        soup = BeautifulSoup(html_content, 'html.parser')

        # 定位所有 <li> 下的 <a> 标签
        list_items_a = soup.select('a:has(div.text)')

        extracted_data = []
        for item_a in list_items_a:
            relative_href = item_a.get('href')
            # 提取 <a> 标签的 title 属性 (作为 fallback 标题)
            title_attr = item_a.get('title')

            full_url = urljoin(base_url, relative_href) if relative_href else None

            # 提取卡片内部的标题 (h6) 和日期 (p)
            title_text = item_a.select_one('h6').text.strip() if item_a.select_one('h6') else 'N/A'
            date_summary = item_a.select_one('p').text.strip() if item_a.select_one('p') else 'N/A'

            if full_url and (title_attr or title_text != 'N/A'):
                extracted_data.append({
                    'full_url': full_url,
                    'title': title_text ,
                    'date_summary': date_summary
                })


        return extracted_data


    def save_article_file(title,url):
        """将文章内容保存到 [日期]_[清理后的标题].txt 文件。"""
        # 清理标题中的非法字符
        safe_title = re.sub(r'[\\/:*?"<>|]', '', title).strip()
        filename = f"{safe_title}.txt"
        filepath = os.path.join(OUTPUT_DIR, filename)

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"【标题】: {title}\n")
                f.write(f"【网址】: {url}\n\n")

            print(f"🎉 文件已保存: {filepath.replace(OUTPUT_DIR + os.path.sep, '')}")
            return True
        except Exception as e:
            print(f"❌ 文件保存失败 ({filename}): {e}")
            return False

    def update_title_list(all_titles):
        """将所有成功处理的文章标题保存到列表文件。"""
        filepath = os.path.join(OUTPUT_DIR, TITLE_LIST_FILE)

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("--- 文章标题列表 (按爬取顺序) ---\n\n")
                for index, title in enumerate(all_titles):
                    f.write(f"{index + 1}. {title}\n")  # 从 1 开始编号
            print(f"\n✅ 标题列表文件已更新: {filepath}")
        except Exception as e:
            print(f"❌ 标题列表保存失败: {e}")

    # --- 3. 主执行流程 ---

    # 确保输出目录存在
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 1. 爬取并解析列表页
    list_html = fetch_list_page(TARGET_URL, HEADERS)
    news_list = parse_list_page(list_html, BASE_URL)
    print(news_list)
    if not news_list:
        print("\n🚫 未提取到任何文章数据，脚本结束。")
        return

    print(f"\n✨ 准备处理 {len(news_list)} 篇文章详情页 ✨")
    print("=" * 60)

    processed_titles = []

    # 2. 遍历并处理所有文章
    for item in news_list:
        title = item['title']
        url = item['full_url']
        # 仅保存成功提取到正文的文章
        if save_article_file(title, url):
            processed_titles.append(title)
        else:
            print(f"⚠️ 跳过保存 ({title})：未提取到有效正文内容。")

    # 3. 更新标题列表文件
    if processed_titles:
        update_title_list(processed_titles)


# 查询工具

EMBEDDING_MODEL = "text-embedding-3-small"
api_key = os.getenv("OPENAI_API_KEY")
TITLE_LIST_FILE = "../data/text_校园一卡通/text_title_list.txt"
CONTENT_BASE_DIR = os.path.dirname(TITLE_LIST_FILE)

def search_school_card_text(
        query_text: str,
        top_k: int = 3
) -> List[Dict]:
    """
    通过语义搜索从标题列表中检索最相似的标题，并读取对应文件的全文内容。
    """

    # 1. 初始化客户端和读取标题列表
    client = openai.OpenAI(api_key=api_key)

    try:
        with open(TITLE_LIST_FILE, 'r', encoding='utf-8') as f:
            titles_list = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"错误：标题列表文件未找到: {TITLE_LIST_FILE}")
        return []

    if not titles_list:
        print("警告：标题列表为空。")
        return []

    # 2. 生成 Embedding 并计算相似度 (检索步骤)
    all_texts = titles_list + [query_text]
    try:
        response = client.embeddings.create(
            input=all_texts,
            model=EMBEDDING_MODEL
        )
    except Exception as e:
        print(f"Embedding API 调用失败: {e}")
        return []

    title_embeddings = np.array([item.embedding for item in response.data[:-1]])
    query_vector = np.array(response.data[-1].embedding)
    similarity_scores = np.dot(title_embeddings, query_vector)
    ranked_indices = np.argsort(similarity_scores)[::-1]

    # 3. 遍历检索结果，读取全文并组装最终结果
    final_results = []

    for i in range(min(top_k, len(titles_list))):
        index = ranked_indices[i]
        title = titles_list[index]
        score = round(float(similarity_scores[index]), 4)

        cleaned_title = re.sub(r"^\d+\.\s*", "", title)

        # --- 全文读取逻辑 (内联) ---
        file_name = f"{cleaned_title.strip()}.txt"
        full_path = os.path.join(CONTENT_BASE_DIR, file_name)
        print()
        full_content = "内容文件读取失败或不存在。"
        try:
            if os.path.exists(full_path):
                with open(full_path, 'r', encoding='utf-8') as f:
                    full_content = f.read()
            # 否则保持默认错误信息
        except Exception as e:
            full_content = f"读取文件 {file_name} 时发生错误: {e}"
        # --- 全文读取逻辑结束 ---

        # 组装最终字典
        final_results.append({
            "title": cleaned_title.strip(),
            "score": score,
            "content": full_content
        })

    return final_results


# --- 示例调用 ---

if __name__ == '__main__':
    # ⚠️ 请根据您的实际项目结构修改路径


    # 确保 CONTENT_BASE_DIR 能够正确指向文章内容文件所在的目录
    # 例如：如果 text_title_list.txt 和 .txt 文件都在同一个目录，则使用上面的定义

    user_query = "校园卡如何使用微信充值"

    print(f"--- 🚀 检索开始 (查询: '{user_query}') ---")

    results_with_content = search_school_card_text(
        query_text=user_query,
        top_k=2
    )

    if results_with_content:
        for i, res in enumerate(results_with_content):
            print(f"Ranking {i + 1}: (相似度: {res['score']})")
            print(f"  标题: {res['title']}")
            print(f"  全文内容 (前100字): {res['content'][:100]}...")
            print("-" * 35)
    else:
        print("未能找到相似内容或发生错误。")


