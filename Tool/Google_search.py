import os
from googleapiclient.discovery import build
from typing import List, Dict, Optional
from dotenv import load_dotenv

# 加载环境变量 (用于安全存储 API 密钥)
load_dotenv()

# 从环境变量中获取密钥和 CSE ID
# 请确保在您的 .env 文件中设置这些变量
API_KEY = os.getenv("GOOGLE_API_KEY")
CSE_ID = os.getenv("GOOGLE_CSE_ID")


def google_search(query: str, num_results: int = 5) -> List[Dict]:
    """
    使用 Google Custom Search JSON API 执行网络搜索。

    该函数依赖于环境变量 GOOGLE_API_KEY 和 GOOGLE_CSE_ID。

    """
    if not API_KEY or not CSE_ID:
        print("❌ 错误：GOOGLE_API_KEY 或 GOOGLE_CSE_ID 环境变量未设置。")
        return []

    try:
        # 1. 构建服务对象
        service = build(
            "customsearch",
            "v1",
            developerKey=API_KEY
        )

        # 2. 执行搜索请求
        result = service.cse().list(
            q=query,
            cx=CSE_ID,
            num=min(num_results, 10)  # 确保不超过 API 限制的最大值 10
        ).execute()

        # 3. 提取和格式化结果
        search_items = result.get('items', [])

        formatted_results = []
        for item in search_items:
            formatted_results.append({
                "title": item.get("title"),
                "link": item.get("link"),
                "snippet": item.get("snippet")
            })

        return formatted_results

    except Exception as e:
        print(f"❌ Google Search API 调用失败: {e}")
        return []
