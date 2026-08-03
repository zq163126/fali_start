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

    print(f"DEBUG: 正在请求 URL -> {url}")
    print("=== 第一步：请求 Challenge ===")
    
    step1_payload = {
        "action": "start",
        "token": "",
        "update": None,
        "node_id": 5056
    }
    
    resp1 = requests.post(url, json=step1_payload, headers=headers, impersonate="chrome120")
    
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
    print("等待 1 秒...")
    time.sleep(1)
    
    print("=== 第二步：带 Challenge 发送启动指令 ===")
    # 模拟真实浏览器在第二步时的完整提交结构
    step2_payload = {
        "action": "start",
        "token": challenge,
        "update": False,
        "node_id": 5056
    }
    
    resp2 = requests.post(url, json=step2_payload, headers=headers, impersonate="chrome120")
    print("Status:", resp2.status_code)
    print("Response Text:", resp2.text)
    
    try:
        data2 = resp2.json()
    except Exception as e:
        print(f"❌ 第二步响应无法解析为 JSON: {e}")
        exit(1)

    # 兼容处理成功的返回状态（有些面板成功时返回 success: true，或者没有 error 字段）
    if data2.get("success") is True or "error" not in data2 or data2.get("error") is None:
        print("🚀 服务器已成功拉起！")
    else:
        print(f"❌ 启动被拒绝，返回数据: {data2}")
        exit(1)

if __name__ == "__main__":
    main()
