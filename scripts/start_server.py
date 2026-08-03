import os
import json
import urllib.request
import urllib.error
import http.cookiejar

def send_telegram_message(text):
    """独立的 Telegram 消息发送模块"""
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
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url, 
            data=data, 
            headers={"Content-Type": "application/json"}, 
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                print("📬 [Telegram] 消息发送成功。")
    except Exception as e:
        print(f"📬 [Telegram] 请求发生网络错误: {e}")

def main():
    cookie_str = os.environ.get("FALIX_WEB_COOKIE")
    server_id = os.environ.get("FALIX_SERVER_ID") or "2874150"
    
    if not cookie_str:
        print("❌ 错误: 未设置 FALIX_WEB_COOKIE 环境变量")
        exit(1)

    # 修正 API 路径（Pterodactyl面板通常的控制动作接口）
    api_url = f"https://client.falixnodes.net/api/client/servers/{server_id}/startup"
    
    # 使用 CookieJar 完美管理和注入环境变量中的 Cookie
    cj = http.cookiejar.CookieJar()
    for item in cookie_str.split(";"):
        if "=" in item:
            parts = item.strip().split("=", 1)
            if len(parts) == 2:
                name, value = parts
                cookie = http.cookiejar.Cookie(
                    version=0, name=name.strip(), value=value.strip(),
                    port=None, port_specified=False,
                    domain="client.falixnodes.net", domain_specified=True, domain_initial_dot=False,
                    path="/", path_specified=True,
                    secure=True, expires=None, discard=True,
                    comment=None, comment_url=None, rest=None
                )
                cj.set_cookie(cookie)

    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    urllib.request.install_opener(opener)

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": f"https://client.falixnodes.net/server/{server_id}/console",
        "Accept": "application/json, text/plain, */*"
    }

    print("🚀 [API 开机] 开始执行两阶段挑战开机逻辑...")

    try:
        # ==================== 第一步：发送初探请求 (token为空) ====================
        payload_step1 = {
            "action": "start",
            "token": "",
            "update": None,
            "node_id": 5056
        }
        
        print(f"📤 [Step 1] 正在向 {api_url} 发送初始 POST 请求 (空 Token)...")
        req1 = urllib.request.Request(
            api_url, 
            data=json.dumps(payload_step1).encode("utf-8"), 
            headers=headers, 
            method="POST"
        )
        
        response_data_1 = None
        try:
            with urllib.request.urlopen(req1, timeout=15) as res:
                response_body_1 = res.read().decode("utf-8")
                print(f"📥 [Step 1] 收到服务器响应: {response_body_1}")
                response_data_1 = json.loads(response_body_1)
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            print(f"📥 [Step 1] 捕获到 HTTP 响应 (状态码 {e.code}): {error_body}")
            try:
                response_data_1 = json.loads(error_body)
            except:
                raise e

        if response_data_1 and (response_data_1.get("success") == True or response_data_1.get("status") == "success"):
            print("🎉 [Step 1] 一次请求直接开机成功！")
            send_telegram_message(f"🚀 *[FalixNodes] 开机成功*\n\n服务器 ID: `{server_id}` (直接通过初探请求成功)")
            return

        # ==================== 第二步：解析 Challenge 并二次提交 ====================
        challenge_token = None
        if response_data_1:
            challenge_token = response_data_1.get("challenge") or response_data_1.get("token") or response_data_1.get("data", {}).get("challenge")

        if not challenge_token:
            print(f"⚠️ [Step 1] 未能自动提取到 challenge 字段，完整返回内容: {response_data_1}")
            msg = f"❌ *[FalixNodes] 开机失败*\n\n未能在第一步响应中找到 challenge 凭证。\n返回数据: `{str(response_data_1)[:200]}`"
            send_telegram_message(msg)
            exit(1)

        print(f"🔑 [Step 2] 成功获取到动态 Challenge Token: {challenge_token}")
        print("📤 [Step 2] 正在携带 Challenge Token 发送二次 POST 请求...")

        payload_step2 = {
            "action": "start",
            "token": challenge_token,
            "update": None,
            "node_id": 5056
        }

        req2 = urllib.request.Request(
            api_url, 
            data=json.dumps(payload_step2).encode("utf-8"), 
            headers=headers, 
            method="POST"
        )

        with urllib.request.urlopen(req2, timeout=15) as res2:
            response_body_2 = res2.read().decode("utf-8")
            print(f"📥 [Step 2] 服务器最终响应: {response_body_2}")
            
            success_msg = f"🚀 *[FalixNodes] 两阶段 API 开机成功*\n\n服务器 ID: `{server_id}`\n已通过 Challenge 验证并成功触发开机！"
            print("🎉 开机指令完整交互成功！")
            send_telegram_message(success_msg)

    except Exception as e:
        error_msg = f"💥 *[FalixNodes] API 开机脚本崩溃*\n\n错误信息: `{str(e)}`"
        print(f"❌ 发生异常: {e}")
        send_telegram_message(error_msg)
        exit(1)

if __name__ == "__main__":
    main()
