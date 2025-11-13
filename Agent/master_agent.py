from ..prompt.Master_prompt import get_master_prompt


# 先注册工具的schema
# 1. 定义google工具
google_search_tool_schema = {
    "type": "function",
    "function": {
        "name": "google_search",
        "description": "用于获取实时信息或最新事件的工具，可以查询关于学校的信息，网络实时新闻等。输入是需要查询的内容。",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "希望搜索的精确关键词或短语，例如：'今天的天气' 或 '2024年巴黎奥运会金牌榜'。",
                }
            },
            "required": ["query"],
        },
    }
}

# 2. 定义(作为独立的 Python 字典)
pass


# 3. 构建正确的工具列表
tools_schema = [
    google_search_tool_schema,
]

tools = []
class Master_Agent:
    def __init__(self):
        self.prompt = get_master_prompt()