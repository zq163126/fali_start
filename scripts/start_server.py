import os
import time
from playwright.sync_api import sync_playwright

def main():
    cookie = os.environ.get("FALIX_WEB_COOKIE")
    server_id = os.environ.get("FALIX_SERVER_ID") or "2874150"
    
    if not cookie:
        print("❌ 错误: 未设置 FALIX_WEB_COOKIE 环境变量")
        exit(1)

    console_url = f"https://client.falixnodes.net/server/{server_id}/console"
    
    # 解析 Cookie 字符串并转换为 Playwright 格式
    cookies = []
    for item in cookie.split(";"):
        if "=" in item:
            name, value = item.strip().split("=", 1)
            cookies.append({
                "name": name,
                "value": value,
                "domain": ".falixnodes.net",
                "path": "/"
            })

    print("🚀 正在启动无头浏览器...")
    with sync_playwright() as p:
        # 启动 Chromium，不使用无头模式可以注释掉 headless=True（但在 CI 里必须为 True）
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        
        # 注入 Cookie
        context.add_cookies(cookies)
        
        page = context.new_page()
        print(f"📄 正在打开控制台页面: {console_url}")
        
        try:
            # 访问页面并等待网络空闲，确保广告 SDK 和控制台完全加载
            page.goto(console_url, wait_until="networkidle", timeout=60000)
        except Exception as e:
            print(f"⚠️ 页面加载超时或警告: {e}")

        time.sleep(3) # 留出时间让广告脚本和初始化加载完成
        
        print("🔍 正在寻找并点击‘启动’按钮...")
        
        # 尝试通过常见的文本或选择器寻找开机/启动按钮
        # 你可以根据实际网页上的按钮文本（如 "Start", "开机", "启动"）调整定位器
        start_button_selectors = [
            "button:has-text('Start')",
            "button:has-text('启动')",
            "button:has-text('开机')",
            "[data-icon='play']",
            ".fa-play"
        ]
        
        clicked = False
        for selector in start_button_selectors:
            try:
                btn = page.locator(selector).first
                if btn.is_visible(timeout=3000):
                    btn.click()
                    print(f"✅ 成功点击启动按钮 (匹配选择器: {selector})")
                    clicked = True
                    break
            except Exception:
                continue
                
        if not clicked:
            print("⚠️ 未能通过选择器自动找到按钮，尝试直接执行 JS 触发开机逻辑...")
            # 也可以在这里通过 fetch 脚本在已有页面上下文中直接跑，此时页面已经加载了所有广告埋点
            page.evaluate(f"""
                async () => {{
                    const res = await fetch('/api/v1/servers/{server_id}/console/power', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ action: 'start', token: '', update: null, node_id: 5056 }})
                    }});
                    const data = await res.json();
                    if (data.challenge) {{
                        // 如果有 challenge，自动请求第二步
                        await fetch('/api/v1/servers/{server_id}/console/power', {{
                            method: 'POST',
                            headers: {{ 'Content-Type': 'application/json' }},
                            body: JSON.stringify({{ action: 'start', token: data.challenge, update: null, node_id: 5056 }})
                        }});
                    }}
                }}
            """)
        
        # 等待几秒观察结果
        time.sleep(5)
        print("📸 当前页面截图保存为 debug.png")
        page.screenshot(path="debug.png")
        
        browser.close()
        print("🚀 流程执行完毕！")

if __name__ == "__main__":
    main()
