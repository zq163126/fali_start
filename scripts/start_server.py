import os
import time
from curl_cffi import requests

def send_telegram_message(text):
    """独立的 Telegram 消息发送模块"""
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
        res = requests.post(url, json=payload, timeout=10)
        if res.status_code == 200:
            print("📬 [Telegram] 报警通知发送成功。")
        else:
            print(f"📬 [Telegram] 通知发送失败，状态码: {res.status_code}")
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
                
                // 2. 兜底策略：移除所有包含 google_ads_iframe 或 class 带有 ad 的遮罩层
                const allAds = document.querySelectorAll("div[id*='google_ads_iframe'], iframe[src*='googlesyndication']");
                allAds.forEach(el => {
                    let parent = el.closest('div');
                    if (parent) parent.remove();
                    else el.remove();
                });
            }
        """)
        print("✨ [广告清理] 广告元素清除函数执行完毕。")
    except Exception as e:
        print(f"⚠️ [广告清理] 清除广告时出现异常: {e}")

def main():
    cookie = os.environ.get("FALIX_WEB_COOKIE")
    server_id = os.environ.get("FALIX_SERVER_ID") or "2874150"
    
    if not cookie:
        print("❌ 错误: 未设置 FALIX_WEB_COOKIE 环境变量")
        exit(1)

    url = f"https://client.falixnodes.net/api/v1/servers/{server_id}/console/power"
    
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "zh-CN,zh;q=0.9,en-US;q=0.8,en-US;q=0.7",
        "cache-control": "no-cache",
        "content-type": "application/json",
        "cookie": cookie,
        "pragma": "no-cache",
        "referer": f"https://client.falixnodes.net/server/{server_id}/console",
        "sec-ch-ua": '"Not;A=Brand";v="8", "Chromium";v="150", "Google Chrome";v="150"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36"
    }

    payload = {
        "action": "start",
        "token": "",
        "update": None,
        "node_id": 5056
    }

    print(f"DEBUG: 正在发送开机请求 -> {url}")
    
    resp = requests.post(url, json=payload, headers=headers, impersonate="chrome120")
    
    print("Status:", resp.status_code)
    print("Response Text:", resp.text)
    
    try:
        data = resp.json()
    except Exception as e:
        print(f"❌ 响应无法解析为 JSON: {e}")
        msg = f"❌ **[FalixNodes] 启动异常**\n\n**服务器 ID:** `{server_id}`\n**错误:** 响应无法解析为 JSON: `{e}`"
        send_telegram_message(msg)
        exit(1)
        
    if resp.status_code == 200 and ("error" not in data or data.get("error") is None):
        print("🚀 服务器已成功拉起！")
        msg = f"🚀 **[FalixNodes] Minecraft 服务器自动拉起成功**\n\n**服务器 ID:** `{server_id}`\n**状态:** 🚀 服务器已成功拉起！"
        send_telegram_message(msg)
    else:
        print(f"❌ 启动失败，返回数据: {data}")
        msg = f"❌ **[FalixNodes] 启动失败**\n\n**服务器 ID:** `{server_id}`\n**返回数据:** `{data}`"
        send_telegram_message(msg)
        exit(1)

if __name__ == "__main__":
    main()
