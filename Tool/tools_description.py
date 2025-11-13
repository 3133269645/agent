tools_description = [
    {
        "type": "function",
        "function": {
            "name": "google_search",
            "description": "调用 Google 自定义搜索 API，获取最新的网页结果。适用于查询校外资讯、背景知识、新闻等公开信息。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "需要检索的关键词或问题，例如 '深圳技术大学招生简章'。"
                    },
                    "num_results": {
                        "type": "integer",
                        "description": "期望返回的搜索结果数量（最大 10，默认 5）。"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_jiaodian_news",
            "description": "在已离线保存的“技大焦点”新闻标题列表中执行语义检索，返回与查询最相关的标题及相似度。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query_text": {
                        "type": "string",
                        "description": "用户希望检索的话题或关键词，例如 '校运会'、'竞赛获奖'。"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "返回的相似标题数量，默认 3，最大建议 10。"
                    }
                },
                "required": ["query_text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_school_card_text",
            "description": "在已整理的“校园一卡通”文章标题列表中执行语义检索，以快速定位相关办事指南或通知,针对的服务是校园卡相关信息获取",
            "parameters": {
                "type": "object",
                "properties": {
                    "query_text": {
                        "type": "string",
                        "description": "要查询的关键词或问题，例如 '校园卡充值'、'挂失流程'。"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "返回的匹配数量"
                    }
                },
                "required": ["query_text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_library_data",
            "description": "访问图书馆系统公开接口，获取给定关键词的自动补全建议及主题推荐信息。",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "要检索的书籍或主题关键词，例如 '人工智能'。"
                    }
                },
                "required": ["keyword"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_jiaowu_score",
            "description": "通过教务系统登录后抓取成绩页面，解析并返回成绩表数据。需要提供有效的学号和密码。",
            "parameters": {
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "description": "教务系统登录账号，通常为学号。"
                    },
                    "password": {
                        "type": "string",
                        "description": "教务系统登录密码。"
                    }
                },
                "required": ["username", "password"]
            }
        }
    }
]
