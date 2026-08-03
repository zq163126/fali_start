import os
import time
from curl_cffi import requests

def main():
    cookie = os.environ.get("FALIX_WEB_COOKIE")
    server_id = os.environ.get("FALIX_SERVER_ID") or "2874150"
    
    if not cookie:
        print("❌ 错误: 未设置 FALIX_WEB_COOKIE 环境变量")
        exit(1)

    url = f"https://client.falixnodes.net/api/v1/servers/{server_id}/console/power"
    page_url = f"https://client.falixnodes.net/server/{server_id}/console"
    
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "zh-CN,zh;q=0.9,en-US;q=0.8,en-US;q=0.7",
        "cache-control": "no-cache",
        "content-type": "application/json",
        "cookie": cookie,
        "pragma": "no-cache",
        "referer": page_url,
        "sec-ch-ua": '"Not;A=Brand";v="8", "Chromium";v="150", "Google Chrome";v="150"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36"
    }

    print(f"DEBUG: 正在初始化 Session 并访问控制台页面 -> {page_url}")
    session = requests.Session()
    
    # 1. 先模拟浏览器“打开控制台页面”，让前端 Cookie/Token 完整生效
    page_headers = headers.copy()
    page_headers["accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"
    page_headers["sec-fetch-dest"] = "document"
    page_headers["sec-fetch-mode"] = "navigate"
    page_headers["sec-fetch-site"] = "same-origin"
    page_headers.pop("content-type", None)
    
    try:
        session.get(page_url, headers=page_headers, impersonate="chrome120")
    except Exception as e:
        print(f"⚠️ 访问主页警告 (可忽略): {e}")

    time.sleep(1)

    print("=== 第一步：请求 Challenge ===")
    step1_payload = {
        "action": "start",
        "token": "",
        "update": None,
        "node_id": 5056
    }
    
    resp1 = session.post(url, json=step1_payload, headers=headers, impersonate="chrome120")
    
    print("Status:", resp1.status_code)
    print("Response Text:", resp1.text)
    
    try:
        data1 = resp1.json()
    except Exception as e:
        print(f"❌ 响应无法解析为 JSON: {e}")
        exit(1)
        
    challenge = data1.get("challenge")
    
    if not challenge:
        print("❌ 未能获取到 challenge，开机失败。")
        exit(1)
        
    print("-" * 30)
    print(f"成功获取 Challenge: {challenge}")
    print("等待 0.5 秒...")
    time.sleep(0.5)
    
    print("=== 第二步：带 Challenge 发送启动指令 ===")
    step2_payload = {
        "action": "start",
        "token": challenge,
        "update": None,
        "node_id": 5056
    }
    
    resp2 = session.post(url, json=step2_payload, headers=headers, impersonate="chrome120")
    print("Status:", resp2.status_code)
    print("Response Text:", resp2.text)
    
    try:
        data2 = resp2.json()
    except Exception as e:
        print(f"❌ 第二步响应无法解析为 JSON: {e}")
        exit(1)

    if data2.get("success") is True or "error" not in data2 or data2.get("error") is None:
        print("🚀 服务器已成功拉起！")
    else:
        print(f"❌ 启动被拒绝，返回数据: {data2}")
        exit(1)

if __name__ == "__main__":
    main()
