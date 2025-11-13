import logging
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional

LOG_DIR_STRUCTURE = ["Logs", "log"]
LOG_LEVEL = logging.INFO

def setup_logging(base_script_path: Optional[str] = None) -> logging.Logger:
    # 1. 确定主执行脚本的路径和名称
    if base_script_path is None:
        try:
            base_script_path = os.path.abspath(sys.argv[0])
        except (IndexError, AttributeError):
            base_script_path = os.getcwd()

    SCRIPT_DIR = os.path.dirname(base_script_path)

    # 获取文件名基准：可以根据需要设置为 'logs' 或 SCRIPT_NAME
    SCRIPT_NAME = os.path.basename(sys.argv[0]).replace(".py", "")

    # 2. 构造动态文件名
    CURRENT_TIME_STR = datetime.now().strftime("%Y-%m-%d_%H_%M")
    LOG_FILE_NAME = f"{CURRENT_TIME_STR}_{SCRIPT_NAME}.log"

    # 3. 完整的日志文件路径
    # 使用 *LOG_DIR_STRUCTURE 将 Logs 和 log 目录添加到路径中
    LOG_DIR_ABS = os.path.join(SCRIPT_DIR, *LOG_DIR_STRUCTURE)  # 关键修正点
    LOG_PATH = os.path.join(LOG_DIR_ABS, LOG_FILE_NAME)

    # 4. 确保日志目录存在
    if not os.path.exists(LOG_DIR_ABS):
        os.makedirs(LOG_DIR_ABS)

    # 5. 创建 Logger 对象
    logger = logging.getLogger('FileOnlyLogger')
    logger.setLevel(LOG_LEVEL)

    # 6. 检查并清理现有的 handlers，防止日志重复记录
    if logger.hasHandlers():
        logger.handlers.clear()

    # 7. 创建 FileHandler
    file_handler = logging.FileHandler(LOG_PATH, mode='a', encoding='utf-8')
    file_handler.setLevel(LOG_LEVEL)

    # 8. 创建 Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )
    file_handler.setFormatter(formatter)

    # 9. 添加 Handler
    logger.addHandler(file_handler)

    # 10. 实现控制台无输出
    logger.propagate = False

    return logger