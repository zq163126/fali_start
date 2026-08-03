import os
import time
import json
import urllib.request
import urllib.error
from playwright.sync_api import sync_playwright

def send_telegram_message(text):
    """独立的 Telegram 消息发送模块（使用 Python 自带的 urllib，无需安装 requests）"""
    tg_token = os.environ.get("TG_BOT_TOKEN")
    chat_id = os.environ.get("TG_CHAT_ID")
    if not tg_token or not chat_id:
        print("ℹ️ 未配置 Telegram 环境变量 (TG_BOT_TOKEN / TG_CHAT_ID)，跳过通知发送。")
        return
        
    url = f"https://api.telegram.org/bot{tg_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url, 
            data=data, 
            headers={"Content-Type": "application/json"}, 
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                print("📬 [Telegram] 报警通知发送成功。")
            else:
                print(f"📬 [Telegram] 通知发送失败，状态码: {response.status}")
    except Exception as e:
        print(f"📬 [Telegram] 请求发生网络错误: {e}")

def remove_ad_element(page):
    """
    清除广告的函数：通过 JavaScript 查找并彻底移除指定的谷歌广告容器 DIV 元素
    """
    print("🧹 [广告清理] 正在尝试清除页面中的广告遮罩层...")
    try:
        page.evaluate("""
            () => {
                // 1. 通过具体的广告容器 ID 直接精准删除
                const adDiv = document.getElementById('google_ads_iframe_/22152718,22541062400/falixnodes_web_interstitial_0__container__');
                if (adDiv) {
                    adDiv.remove();
                }
                
                // 2. 兜底策略：移除所有包含 google_ads_iframe 或 safeframe 的遮罩层
                const allAds = document.querySelectorAll("div[id*='google_ads_iframe'], iframe[src*='googlesyndication'], iframe[src*='safeframe']");
                allAds.forEach(el => {
                    let parent = el.closest('div');
                    if (parent && parent !== document.body) {
                        parent.remove();
                    } else {
                        el.remove();
                    }
                });
            }
        """)
        print("✨ [广告清理] 广告元素清除函数执行完毕。")
    except Exception as e:
        print(f"⚠️ [广告清理] 清除广告时出现异常: {e}")

def main():
    cookie_str = os.environ.get("FALIX_WEB_COOKIE")
    server_id = os.environ.get("FALIX_SERVER_ID") or "2874150"
    
    if not cookie_str:
        print("❌ 错误: 未设置 FALIX_WEB_COOKIE 环境变量")
        exit(1)

    console_url = f"https://client.falixnodes.net/server/{server_id}/console"
    print(f"🌐 正在打开控制面板页面: {console_url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36"
        )

        # 解析并注入 Cookie
        cookies_list = []
        for item in cookie_str.split(";"):
            if "=" in item:
                parts = item.strip().split("=", 1)
                if len(parts) == 2:
                    name, value = parts
                    cookies_list.append({
                        "name": name.strip(),
                        "value": value.strip(),
                        "domain": ".falixnodes.net",
                        "path": "/"
                    })
        if cookies_list:
            context.add_cookies(cookies_list)

        page = context.new_page()

        try:
            # 访问控制台页面
            page.goto(console_url, wait_until="domcontentloaded", timeout=60000)
            time.sleep(5)  # 等待页面加载

            # 1. 在进行任何点击前，必须先调用清除广告函数
            remove_ad_element(page)
            time.sleep(1)

            # 2. 使用完全摒弃随机 ID、鲁棒性极强的多维选择器定位 START 按钮
            print("🖱️ 正在寻找并点击 START 按钮...")
            
            # 策略组合：匹配 class 带有 "console-btn start" 且内部包含文本“启动”的按钮
            start_btn = page.locator("button.console-btn.start").filter(has_text="启动")
            
            # 如果没找到，再提供一层基于 XPath 结构特征的通用兜底
            if not start_btn.count():
                start_btn = page.locator("//button[contains(@class, 'console-btn') and contains(@class, 'start') and .//span[text()='启动']]")

            if start_btn.count() > 0:
                # 确保按钮可见并可点击，使用 force=True 应对潜在防呆遮挡
                start_btn.first.click(force=True, timeout=10000)
                print("🚀 成功触发 START 按钮点击！")
                
                time.sleep(3) # 等待后端响应
                
                msg = f"🚀 **[FalixNodes] 网页自动化开机成功**\n\n**服务器 ID:** `{server_id}`\n**动作:** 已通过鲁棒性选择器成功点击网页 `START` 按钮。"
                send_telegram_message(msg)
            else:
                print("❌ 未能在页面上找到 START 按钮元素。")
                msg = f"❌ **[FalixNodes] 开机失败**\n\n**服务器 ID:** `{server_id}`\n**原因:** 未能在页面上找到 START 按钮元素。"
                send_telegram_message(msg)
                exit(1)

        except Exception as e:
            error_msg = f"❌ 自动化执行过程中发生异常: {str(e)}"
            print(error_msg)
            msg = f"💥 **[FalixNodes] 运行崩溃**\n\n**错误:** `{str(e)}`"
            send_telegram_message(msg)
            exit(1)
        finally:
            browser.close()

if __name__ == "__main__":
    main()
