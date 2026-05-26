import os
import time
from playwright.sync_api import sync_playwright

def run(playwright):
    # 从环境变量读取登录信息
    username = os.environ.get('ACL_USERNAME', '')
    password = os.environ.get('ACL_PASSWORD', '')

    if not username or not password:
        print("错误: 请在GitHub Secrets中设置ACL_USERNAME和ACL_PASSWORD。")
        return

    # 启动浏览器 (无头模式)
    browser = playwright.chromium.launch(headless=True)
    # 创建上下文，添加一个更真实的User-Agent
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    page = context.new_page()

    try:
        print("1. 正在访问登录页面...")
        # 访问登录页面。请将 'login-url' 替换为ACLClouds实际的登录页面地址
        page.goto("https://dash.aclclouds.com/login", timeout=60000)
        page.wait_for_timeout(3000)  # 等待页面稳定
        page.screenshot(path="step_1_login_page.png", full_page=True)

        # --- 2. 执行登录操作 ---
        print("2. 正在尝试登录...")
        # 请根据登录页面的实际HTML结构调整选择器
        # 常见的用户名/邮箱输入框选择器
        username_selector = "input[name='email'], input[type='email'], input[placeholder*='邮箱'], input[placeholder*='Email']"
        # 常见的密码输入框选择器
        password_selector = "input[name='password'], input[type='password'], input[placeholder*='密码'], input[placeholder*='Password']"
        # 常见的登录按钮选择器
        login_button_selector = "button[type='submit'], button:has-text('登录'), button:has-text('Login')"

        # 等待输入框出现
        page.wait_for_selector(username_selector, timeout=10000)
        page.fill(username_selector, username)
        page.fill(password_selector, password)

        # 截图确认填写情况
        page.screenshot(path="step_2_login_form_filled.png", full_page=True)
        # 点击登录按钮
        page.click(login_button_selector)

        # 等待登录完成并跳转，通过检查URL或等待特定元素来判断
        page.wait_for_timeout(5000)  # 等待页面跳转
        print(f"   登录后，当前URL: {page.url}")
        page.screenshot(path="step_3_after_login.png", full_page=True)

        # --- 3. 导航到项目面板并续期 ---
        print("3. 导航到项目面板...")
        # 目标面板地址
        projects_url = "https://dash.aclclouds.com/projects"
        page.goto(projects_url, timeout=60000)
        page.wait_for_timeout(5000)  # 等待页面加载完成

        # 截图以查看当前页面
        page.screenshot(path="step_4_projects_page.png", full_page=True)

        # 续期按钮文本 (根据你提供的截图，按钮文本是 'Renouveler')
        renew_text = "Renouveler"

        # 查找所有包含指定文本的按钮
        renew_buttons = page.locator(f"button:has-text('{renew_text}')")
        count = renew_buttons.count()

        if count == 0:
            print(f"未找到 '{renew_text}' 按钮。请查看截图确认页面状态。")
            # 如果没找到，尝试查找所有包含 "Renew" 或 "续期" 字样的元素
            fallback_buttons = page.locator("button:has-text('Renew'), button:has-text('续期'), text='Renouveler'")
            fallback_count = fallback_buttons.count()
            if fallback_count > 0:
                print(f"   但使用宽泛查找找到了 {fallback_count} 个可能的按钮。")
                renew_buttons = fallback_buttons
                count = fallback_count
            else:
                return

        print(f"找到 {count} 个 '{renew_text}' 按钮，准备点击续期...")
        for i in range(count):
            button = renew_buttons.nth(i)
            if button.is_visible():
                button.click()
                print(f"   已点击第 {i+1} 个按钮。")
                page.wait_for_timeout(3000)  # 每次点击后稍等片刻

        # 续期操作完成后的截图
        page.screenshot(path="step_5_after_renew.png", full_page=True)
        print("任务执行完毕。")

    except Exception as e:
        print(f"执行过程中发生错误: {e}")
        # 出错时进行截图，便于排查问题
        page.screenshot(path="error_screenshot.png", full_page=True)

    finally:
        browser.close()

with sync_playwright() as playwright:
    run(playwright)
