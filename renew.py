import os
from playwright.sync_api import sync_playwright

RENEW_TEXTS = [
    "Renouveler",  # FR 法语
    "Renew",       # EN 英语
    "Erneuern",    # DE 德语
    "Renovar",     # ES/PT 西班牙语/葡萄牙语
    "Обновить",    # RU 俄语
    "Rinnova",     # IT 意大利语
]

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context(
        # 伪装一下 User-Agent，降低被拦截的概率
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    raw_cookies = os.environ.get('ACL_COOKIES', '')
    if not raw_cookies:
        print("错误: 未找到 ACL_COOKIES 环境变量。")
        return

    cookies = []
    for item in raw_cookies.split(';'):
        if '=' in item:
            name, value = item.split('=', 1)
            cookies.append({
                "name": name.strip(),
                "value": value.strip(),
                "domain": "dash.aclclouds.com",
                "path": "/"
            })

    context.add_cookies(cookies)
    page = context.new_page()

    try:
        print("正在访问项目面板...")
        page.goto("https://dash.aclclouds.com/projects", timeout=60000)
        
        # 强制等待 5 秒，确保前端 React/Vue 等框架把按钮渲染出来
        page.wait_for_timeout(5000)

        # 核心调试步骤：截取当前页面的完整长图
        print("正在保存页面截图以供排查...")
        page.screenshot(path="debug_page.png", full_page=True)
        print("截图保存成功: debug_page.png")

        # 放宽查找条件，只要包含 Renew 文本的元素都找出来
        total_clicked = 0
        for text in RENEW_TEXTS:
            buttons = page.locator(f"text='{text}'")
            count = buttons.count()
            if count > 0:
                print(f"找到按钮文字 '{text}'，共 {count} 个，开始点击...")
                for i in range(count):
                    btn = buttons.nth(i)
                    if btn.is_visible():
                        btn.click()
                        total_clicked += 1
                        print(f"已点击第 {total_clicked} 个续期按钮（{text}）。")
                        page.wait_for_timeout(3000)

        if total_clicked == 0:
            print("未找到任何续期按钮，请查看截图确认页面状态。")
        else:
            print(f"共点击了 {total_clicked} 个续期按钮。")
            page.screenshot(path="debug_page_after_click.png", full_page=True)

        print("任务执行完毕。")

    except Exception as e:
        print(f"执行过程中发生错误: {e}")
        # 出错时也尝试截图
        page.screenshot(path="error_page.png", full_page=True)
    finally:
        browser.close()

with sync_playwright() as playwright:
    run(playwright)
