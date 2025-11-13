import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os
import re
import openai
import numpy as np
from typing import List, Dict
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


# --- 工具函数：爬虫脚本封装 ---
def run_sztu_news_spider():
    """
    爬取深圳技术大学 (sztu.edu.cn) '技大焦点' 板块的新闻内容。
    将新闻详情保存为单独的 .txt 文件，并生成一个标题列表文件。
    该函数无任何入参，直接调用即可触发整个爬虫流程。
    """

    # --- 1. 定义常量 ---
    BASE_URL = "https://www.sztu.edu.cn/"
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36 Edg/141.0.0.0'
    }
    OUTPUT_DIR = "./data/text_技大焦点"
    TITLE_LIST_FILE = "text_title_list.txt"  # 标题列表文件名

    # --- 2. 辅助函数定义 ---

    def fetch_list_page(url, headers):
        """请求列表页 HTML 内容。"""
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        response.encoding = 'utf-8'
        return response.text

    def parse_list_page(html_content):
        """从列表页提取新闻标题、摘要和完整链接。"""
        if not html_content:
            return []

        soup = BeautifulSoup(html_content, 'html.parser')
        list_items = soup.select('li > a')

        extracted_data = []
        for item_a in list_items:
            relative_href = item_a.get('href')
            full_url = urljoin(BASE_URL, relative_href) if relative_href else None

            h3_tag = item_a.select_one('.yy-ifo h3')
            title = h3_tag.text.strip() if h3_tag else 'N/A'

            p_tag = item_a.select_one('.yy-ifo p')
            summary = p_tag.text.strip() if p_tag else 'N/A'

            if full_url and title != 'N/A':
                extracted_data.append({
                    'full_url': full_url,
                    'title': title,
                    'summary': summary
                })
        return extracted_data

    def fetch_detail_page_and_parse(url, headers):
        """请求详情页，精确提取并清洗新闻正文。"""
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')

        # 精确地定位新闻正文内容区域的父级容器
        content_container = soup.find(class_='content-pg')
        if not content_container:
            content_container = soup.find('form', attrs={'name': '_newscontent_fromname'})
        if not content_container:
            return None, "N/A"

        # 1. 提取文章发布日期
        date_p = content_container.find('div', class_='c-ifo')
        if date_p:
            date_match = re.search(r'时间:\s*(\d{4}/\d{2}/\d{2})', date_p.get_text())
            date_str = date_match.group(1).replace('/', '-') if date_match else "未知日期"

        # 2. 清洗正文内容
        all_paragraphs = content_container.find_all('p')
        cleaned_text_lines = []
        EXCLUDE_CLASSES = ['flex', 'bounce']
        EXCLUDE_TEXTS = ['信息来源:', '供稿', '编辑', '浏览量:', '图片来源', 'HIGHLIGHTS']

        for p_tag in all_paragraphs:
            p_text = p_tag.get_text(strip=True)
            tag_classes = p_tag.get('class', [])

            # 过滤掉辅助信息、空行及特殊关键词
            if not p_text or any(cls in tag_classes for cls in EXCLUDE_CLASSES) or \
                    any(text_fragment in p_text for text_fragment in EXCLUDE_TEXTS) or \
                    re.match(r'^\d{4}-\d{2}-\d{2}$', p_text):
                continue

            # 排除信息栏中的重复段落
            if date_p and date_p.find(text=p_text, recursive=True):
                continue

            cleaned_text_lines.append(p_text)

        full_content = "\n\n".join(cleaned_text_lines)
        return full_content, date_str

    def save_article_file(title, content):
        """将文章内容保存到以 [日期]_[标题].txt 命名的文件。"""
        # 清理标题中的非法字符
        safe_title = re.sub(r'[\\/:*?"<>|]', '', title).strip()

        # 构造文件名和路径
        filename = f"{safe_title}.txt"
        filepath = os.path.join(OUTPUT_DIR, filename)

        # 检查文件是否已存在，如果存在则跳过（避免重复爬取）
        if os.path.exists(filepath):
            print(f"⚠️ 文章已存在，跳过爬取: {filename}")
            return False  # 返回 False 表示未进行新的保存

        with open(filepath, 'w', encoding='utf-8') as f:
            # 在文件开头添加标题和日期，保持清晰结构
            f.write(f"【标题】: {title}\n")
            f.write(f"【日期】: {date_str}\n\n")
            f.write(content)
        print(f"🎉 文章文件已成功保存: {filepath}")
        return True  # 返回 True 表示进行了新的保存


    def update_title_list(new_titles):
        """将新提取到的标题追加保存到 text_title_list.txt 文件中。"""
        filepath = os.path.join(OUTPUT_DIR, TITLE_LIST_FILE)

        # 确定起始编号 (用于追加时的正确序号)
        current_titles_count = 0
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                # 简单计算当前文件已有的标题数量，以便从正确的序号开始追加
                for line in f:
                    if re.match(r'^\d+\.', line.strip()):
                        current_titles_count += 1

        # 核心：使用追加模式 'a' 打开文件
        with open(filepath, 'a', encoding='utf-8') as f:
            # 如果文件是空的或不存在，则添加头部
            if current_titles_count == 0:
                f.write("--- 文章标题列表 ---\n\n")

            start_index = current_titles_count + 1
            for index, title in enumerate(new_titles):
                f.write(f"{start_index + index}. {title}\n")

        print(f"\n✅ {len(new_titles)} 个新标题已追加到列表文件: {filepath}")

    # --- 主执行逻辑 ---

    # 确保输出目录存在
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 用于保存本次运行中成功新增的文章标题
    newly_processed_titles = []

    # 1. 爬取列表页 (修正循环逻辑，避免覆盖)
    print("✨ 开始爬取新闻列表页，处理新的文章...")

    for i in range(1, 108):
        try:
            TARGET_URL = urljoin(BASE_URL, f"jdjd/xyxw/{i}.htm")
            print(f"--- 正在处理列表页: {TARGET_URL} ---")

            list_html = fetch_list_page(TARGET_URL, HEADERS)
            news_list = parse_list_page(list_html)

            if not news_list:
                print("🚫 未提取到任何新闻数据或已达列表末尾。")
                break  # 列表为空，可能爬取完毕，退出循环

            # 2. 遍历并处理所有新闻
            for item in news_list:
                title = item['title']
                full_url = item['full_url']

                # 3. 爬取详情页并提取纯文本内容及日期
                content, date_str = fetch_detail_page_and_parse(full_url, HEADERS)

                # 4. 保存文件并记录标题 (save_article_file 内部会检查重复)
                if content and content.strip():
                    if save_article_file(title, content):
                        # 只有成功保存的新文章才加入列表
                        newly_processed_titles.append(title)
                else:
                    print(f"⚠️ 跳过保存 ({title})：详情页内容提取失败或为空。")

        except requests.RequestException as e:
            print(f"❌ 列表页 {TARGET_URL} 请求失败，跳过: {e}")
            continue

    # 5. 统一更新标题列表文件 (使用追加模式)
    if newly_processed_titles:
        update_title_list(newly_processed_titles)
        print(f"\n🎉 爬虫流程结束，共新增 {len(newly_processed_titles)} 篇文章。")
    else:
        print("\n🎉 爬虫流程结束，本次运行未发现新的文章需要保存。")


# --- 语义搜索工具函数 (保持不变) ---

EMBEDDING_MODEL = "text-embedding-3-small"
api_key = os.getenv("OPENAI_API_KEY")
TITLE_LIST_FILE = "./data/text_技大焦点/text_title_list.txt"
CONTENT_BASE_DIR = os.path.dirname(TITLE_LIST_FILE)

def search_jiaodian_news(
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
    run_sztu_news_spider()
    user_query = "运动会"

    print(f"--- 🚀 检索开始 (查询: '{user_query}') ---")

    results_with_content = search_jiaodian_news(
        query_text=user_query,
        top_k=3
    )

    if results_with_content:
        for i, res in enumerate(results_with_content):
            print(f"Ranking {i + 1}: (相似度: {res['score']})")
            print(f"  标题: {res['title']}")
            print(f"  全文内容 (前100字): {res['content'][:100]}...")
            print("-" * 35)
    else:
        print("未能找到相似内容或发生错误。")