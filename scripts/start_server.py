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

    print(f"DEBUG: 正在请求 URL -> {url}")
    session = requests.Session()
    
    print("=== 发送初始开机请求 ===")
    payload = {
        "action": "start",
        "token": "",
        "update": None,
        "node_id": 5056
    }
    
    resp = session.post(url, json=payload, headers=headers, impersonate="chrome120")
    print("Status:", resp.status_code)
    print("Response Text:", resp.text)
    
    try:
        data = resp.json()
    except Exception as e:
        print(f"❌ 响应无法解析为 JSON: {e}")
        exit(1)
        
    # 情况 1：如果没有触发 ad 错误，说明当前无广告，直接成功！
    if "error" not in data or data.get("error") is None or data.get("success") is True:
        print("🚀 当前无广告拦截，服务器已成功直接拉起！")
        return

    # 情况 2：触发了 ad 挑战
    if data.get("error") == "ad":
        challenge = data.get("challenge")
        print(f"⚠️ 检测到广告挑战，获取到的 Challenge: {challenge}")
        
        print("等待 1 秒...")
        time.sleep(1)
        
        # 尝试带上 NOADDETECTED 或者真实 challenge 再次请求
        # 这里我们可以优先尝试你提到的成功经验："NOADDETECTED"，如果不行也可以用获取到的 challenge
        for test_token in ["NOADDETECTED", challenge]:
            print(f"=== 尝试使用 Token 绕过: {test_token} ===")
            retry_payload = {
                "action": "start",
                "token": test_token,
                "update": None,
                "node_id": 5056
            }
            
            resp_retry = session.post(url, json=retry_payload, headers=headers, impersonate="chrome120")
            print("Retry Status:", resp_retry.status_code)
            print("Retry Response Text:", resp_retry.text)
            
            try:
                data_retry = resp_retry.json()
            except:
                continue
                
            if data_retry.get("success") is True or "error" not in data_retry or data_retry.get("error") is None:
                print(f"🚀 使用 token [{test_token}] 成功绕过并拉起服务器！")
                return

    print("❌ 所有开机尝试均被拒绝。")
    exit(1)

if __name__ == "__main__":
    main()
