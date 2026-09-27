"""测试 Binance 下单 API 并获取详细错误信息"""
import requests
import yaml
import time
import hmac
import hashlib
from urllib.parse import urlencode

# 读取配置
with open('system.yaml', 'r', encoding='utf-8') as f:
    system_config = yaml.safe_load(f)

with open('secrets/account1.key', 'r', encoding='utf-8') as f:
    secrets = yaml.safe_load(f)

api_key = secrets['binance']['api_key']
secret_key = secrets['binance']['secret_key']

# 代理设置
proxy_config = system_config.get("system", {}).get("proxy", {})
proxies = None
if proxy_config.get("enabled", False):
    proxies = {
        "http": proxy_config.get("http"),
        "https": proxy_config.get("https")
    }

print("=" * 60)
print("测试 Binance 下单 API")
print("=" * 60)
print()

# 构造下单请求
params = {
    "symbol": "SPY",
    "side": "BUY",
    "orderType": "MARKET",
    "notional": 6.0,
    "timestamp": int(time.time() * 1000)
}

# 签名
query_string = urlencode(params)
signature = hmac.new(
    secret_key.encode('utf-8'),
    query_string.encode('utf-8'),
    hashlib.sha256
).hexdigest()
params['signature'] = signature

url = "https://api.binance.com/sapi/v1/equity/order/place"
headers = {"X-MBX-APIKEY": api_key}

print(f"请求 URL: {url}")
print(f"请求参数: {params}")
print()

try:
    response = requests.post(
        url,
        headers=headers,
        params=params,
        proxies=proxies,
        timeout=10
    )

    print(f"状态码: {response.status_code}")
    print(f"响应头: {dict(response.headers)}")
    print()

    if response.status_code == 200:
        data = response.json()
        print("[SUCCESS] 下单成功!")
        print(f"订单数据: {data}")
    else:
        print("[FAILED] 下单失败")
        print(f"响应文本: {response.text}")

        try:
            error_data = response.json()
            print(f"\n错误详情:")
            print(f"  错误码: {error_data.get('code')}")
            print(f"  错误信息: {error_data.get('msg')}")
        except:
            pass

except Exception as e:
    print(f"[ERROR] 异常: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 60)
