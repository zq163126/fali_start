import os
import json
from curl_cffi import requests

def send_telegram_message(text):
    """独立 Telegram 通知模块"""
    tg_token = os.environ.get("TG_BOT_TOKEN")
    chat_id = os.environ.get("TG_CHAT_ID")
    if not tg_token or not chat_id:
        print("ℹ️ 未配置 Telegram 环境变量，跳过通知发送。")
        return
        
    url = f"https://api.telegram.org/bot{tg_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        if resp.status_code == 200:
            print("📬 [Telegram] 消息发送成功。")
    except Exception as e:
        print(f"📬 [Telegram] 请求发生网络错误: {e}")

def main():
    cookie = os.environ.get("FALIX_WEB_COOKIE")
    server_id = os.environ.get("FALIX_SERVER_ID") or "2874150"
    
    if not cookie:
        print("❌ 错误: 未设置 FALIX_WEB_COOKIE 环境变量")
        exit(1)

    url = f"https://client.falixnodes.net/api/v1/servers/{server_id}/console/power"
    
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
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

    print(f"🚀 [API 开机] 开始执行两阶段挑战开机逻辑 -> {url}")
    
    try:
        # ==================== 第一步：发送初探请求 (token为空) ====================
        payload_step1 = {
            "action": "start",
            "token": "",
            "update": None,
            "node_id": 5056
        }
        
        print("📤 [Step 1] 正在发送初始 POST 请求 (空 Token)...")
        resp1 = requests.post(url, json=payload_step1, headers=headers, impersonate="chrome120")
        
        print(f"Status (Step 1): {resp1.status_code}")
        print(f"Response Text (Step 1): {resp1.text}")
        
        data1 = resp1.json()
        
        # 检查是否一次直接成功
        if resp1.status_code == 200 and ("error" not in data1 or data1.get("error") is None) and not data1.get("challenge"):
            print("🎉 [Step 1] 一次请求直接开机成功！")
            send_telegram_message(f"🚀 *[FalixNodes] 开机成功*\n\n服务器 ID: `{server_id}` (初探请求直接成功)")
            return

        # ==================== 第二步：解析 Challenge 并二次提交 ====================
        challenge_token = data1.get("challenge") or data1.get("token") or data1.get("data", {}).get("challenge")
        
        if not challenge_token:
            print(f"❌ 未能从响应中提取出 challenge 字段: {data1}")
            send_telegram_message(f"❌ *[FalixNodes] 开机失败*\n\n服务器返回了未知结构：`{str(data1)[:150]}`")
            exit(1)

        print(f"🔑 [Step 2] 成功获取到 Challenge Token: {challenge_token}")
        print("📤 [Step 2] 正在携带 Challenge Token 发送二次 POST 请求...")

        payload_step2 = {
            "action": "start",
            "token": challenge_token,
            "update": None,
            "node_id": 5056
        }

        resp2 = requests.post(url, json=payload_step2, headers=headers, impersonate="chrome120")
        
        print(f"Status (Step 2): {resp2.status_code}")
        print(f"Response Text (Step 2): {resp2.text}")
        
        data2 = resp2.json()
        
        if resp2.status_code == 200 and ("error" not in data2 or data2.get("error") is None):
            print("🚀 [Step 2] 服务器已通过 Challenge 成功拉起！")
            send_telegram_message(f"🚀 *[FalixNodes] 两阶段 API 开机成功*\n\n服务器 ID: `{server_id}`\n已通过验证并成功触发开机！")
        else:
            print(f"❌ 第二阶段启动失败，返回数据: {data2}")
            send_telegram_message(f"❌ *[FalixNodes] 开机失败*\n\n第二阶段验证未通过：`{str(data2)[:150]}`")
            exit(1)

    except Exception as e:
        print(f"❌ 运行过程中发生异常: {e}")
        send_telegram_message(f"💥 *[FalixNodes] 开机脚本崩溃*\n\n错误信息: `{str(e)}`")
        exit(1)

if __name__ == "__main__":
    main()
