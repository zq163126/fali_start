import os
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
        exit(1)
        
    if resp.status_code == 200 and ("error" not in data or data.get("error") is None):
        print("🚀 服务器已成功拉起！")
    else:
        print(f"❌ 启动失败，返回数据: {data}")
        exit(1)

if __name__ == "__main__":
    main()
