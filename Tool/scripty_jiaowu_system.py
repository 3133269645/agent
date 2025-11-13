import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time  # 引入 time 库用于可能的等待
from typing import Dict, List, Optional

# --- 1. 配置信息 ---
YOUR_LOGIN_URL = "https://auth.sztu.edu.cn/idp/authcenter/ActionAuthChain?entityId=jiaowu"
SCORE_URL = "https://jwxt.sztu.edu.cn/jsxsd/kscj/cjcx_list?ccc=0&ss="  # 成绩查询接口



# --- 2. 登录并获取 Cookies 函数 ---

def get_login_cookies(driver, login_url, username, password):
    """
    使用 Selenium 登录，并返回登录成功后的所有 Cookies。
    """
    print(f"打开登录页面: {login_url}")
    driver.get(login_url)

    try:
        # 显式等待用户名输入框出现
        username_field = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "j_username"))
        )
        password_field = driver.find_element(By.ID, "j_password")

        # 输入账号和密码，先清空确保没有默认值
        username_field.clear()
        username_field.send_keys(username)

        password_field.clear()
        password_field.send_keys(password)

        LOGIN_BUTTON_XPATH = "//button[contains(@onclick, 'authen1Form')]"
        login_button = driver.find_element(By.XPATH, LOGIN_BUTTON_XPATH)

        print("尝试点击登录...")
        login_button.click()

        # 等待 URL 跳转到教务系统的 /jsxsd/ 路径，确认登录成功
        WebDriverWait(driver, 20).until(
            EC.url_contains("jsxsd")
        )
        # 增加一个短暂的隐式等待，确保页面完全稳定，特别是 Cookie 完全加载
        time.sleep(2)

        # 提取 Cookies
        cookies = driver.get_cookies()
        print("✅ Selenium 登录成功，Cookies 已提取。")
        return cookies

    except Exception as e:
        print(f"❌ Selenium 登录失败或超时: {e}")
        return None


# --- 3. 使用 Requests 获取数据函数 ---

def get_scores_via_requests(cookies_list):
    """
    将 Selenium Cookies 注入到 requests.Session，并发送 POST 请求获取成绩。
    """
    s = requests.Session()

    # 1. 转换 Cookies 格式并注入到 Session (保持不变)
    for cookie in cookies_list:
        s.cookies.set(cookie['name'], cookie['value'])

    # 2. 构造 POST 请求参数 (Payload) (保持不变)
    SCORE_URL = "https://jwxt.sztu.edu.cn/jsxsd/kscj/cjcx_list?ccc=0&ss="
    payload = {
        'cxfs': '1',
        'kksj': '',
        'kcxz': '',
        'kcmc': '',
        'xsfs': 'all',
    }

    # 3. 构造请求头
    print(f"发送 POST 请求到成绩接口: {SCORE_URL}")
    headers = {
        # 匹配您提供的 Edge 浏览器 User-Agent
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36 Edg/141.0.0.0',

        # ⚠️ 使用您提供的精确 Referer 值
        'Referer': 'https://jwxt.sztu.edu.cn/jsxsd/kscj/cjcx_query?zylx=',

        # 添加其他重要头部以模拟浏览器行为
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Upgrade-Insecure-Requests': '1',
        'Origin': 'https://jwxt.sztu.edu.cn',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Dest': 'iframe',
    }

    response = s.post(SCORE_URL, data=payload, headers=headers)

    if response.status_code == 200:
        print("✅ 成绩查询成功！")
        return response.text
    else:
        print(f"❌ 成绩查询失败，状态码: {response.status_code}")
        print("请检查 POST 请求的 URL、Headers 和 Payload。")
        return None


# --- 4. HTML 解析函数 ---

def parse_score_table(score_html: str) -> List[Dict[str, str]]:
    """
    使用 BeautifulSoup 解析 HTML，提取 dataList 表格中的成绩数据。
    """
    soup = BeautifulSoup(score_html, 'html.parser')

    # 1. 定位到成绩表格
    score_table = soup.find('table', id='dataList')

    if not score_table:
        print("❌ 错误：HTML 中未找到 id='dataList' 表格。")
        return []

    rows = score_table.find_all('tr')

    # 检查是否是空结果 (如 "未查询到数据")
    if '未查询到数据' in score_table.get_text():
        print(f"❗ 提示：查询结果为空。请检查 Payload 中的学年/学期 ('2025-2026-1') 是否有数据。")
        return []

    if len(rows) < 2:
        return []

    # 2. 提取表头 (Header)
    header = [th.get_text(strip=True) for th in rows[0].find_all('th')]

    # 3. 提取数据行 (Data)
    data = []
    # 从第二行开始遍历 (跳过表头)
    for row in rows[1:]:
        cells = row.find_all('td')
        # 确保数据行完整（单元格数量与表头数量一致）
        if cells and len(cells) == len(header):
            row_data = [cell.get_text(strip=True) for cell in cells]
            # 组合成字典列表
            data.append(dict(zip(header, row_data)))

    return data


# --- 5. 主执行流程 ---
def search_jiaowu_score(username: str, password: str) -> Optional[List[Dict[str, str]]]:
    # 初始化 WebDriver
    driver = webdriver.Chrome()

    # 1. 使用 Selenium 登录并获取 Cookies
    cookies = get_login_cookies(driver, YOUR_LOGIN_URL, username, password)

    driver.quit()

    if cookies:
        # 2. 使用 Cookies 发送 Requests 请求获取成绩 HTML
        score_html = get_scores_via_requests(cookies)

        if score_html:
            # 3. 解析成绩 HTML
            return parse_score_table(score_html)

    return None
