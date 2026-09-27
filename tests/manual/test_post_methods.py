"""测试 POST 请求参数传递方式"""
import hmac
import hashlib
import time
import requests
from pathlib import Path
import yaml

# 加载密钥
secrets_file = Path("secrets/account1.key")
with open(secrets_file, "r") as f:
    secrets = yaml.safe_load(f)

binance_config = secrets.get("binance", {})
api_key = binance_config.get("api_key")
secret_key = binance_config.get("secret_key")

print("=" * 70)
print("测试 Binance POST 请求参数传递方式")
print("=" * 70)

endpoint = "/sapi/v1/equity/order/place"
base_url = "https://api.binance.com"

# 下单参数
params = {
    "symbol": "SPY",
    "side": "BUY",
    "orderType": "MARKET",
    "notional": 6.0,
    "timestamp": int(time.time() * 1000)
}

# 生成签名
query_string = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
signature = hmac.new(
    secret_key.encode("utf-8"),
    query_string.encode("utf-8"),
    hashlib.sha256
).hexdigest()

params["signature"] = signature

headers = {
    "X-MBX-APIKEY": api_key
}

proxies = {"http": "http://127.0.0.1:7990", "https": "http://127.0.0.1:7990"}

# 方式 1: 使用 params（query string）
print("\n[方式 1] 使用 params（参数在 URL query string）")
print("-" * 70)
try:
    response = requests.post(
        base_url + endpoint,
        params=params,  # 参数作为 query string
        headers=headers,
        proxies=proxies,
        timeout=10
    )

    print(f"请求 URL: {response.url}")
    print(f"响应状态: {response.status_code}")

    if response.status_code == 200:
        print(f"  [SUCCESS]")
    else:
        try:
            error = response.json()
            print(f"  [ERROR] code={error.get('code')}, msg={error.get('msg')}")
        except:
            print(f"  [ERROR] {response.text[:200]}")
except Exception as e:
    print(f"  [ERROR] {e}")

# 方式 2: 使用 data（request body）
print("\n[方式 2] 使用 data（参数在 request body）")
print("-" * 70)

# 重新生成时间戳和签名
params2 = {
    "symbol": "SPY",
    "side": "BUY",
    "orderType": "MARKET",
    "notional": 6.0,
    "timestamp": int(time.time() * 1000)
}

query_string2 = "&".join([f"{k}={v}" for k, v in sorted(params2.items())])
signature2 = hmac.new(
    secret_key.encode("utf-8"),
    query_string2.encode("utf-8"),
    hashlib.sha256
).hexdigest()

params2["signature"] = signature2

try:
    response = requests.post(
        base_url + endpoint,
        data=params2,  # 参数作为 request body
        headers=headers,
        proxies=proxies,
        timeout=10
    )

    print(f"请求 URL: {response.url}")
    print(f"响应状态: {response.status_code}")

    if response.status_code == 200:
        print(f"  [SUCCESS]")
    else:
        try:
            error = response.json()
            print(f"  [ERROR] code={error.get('code')}, msg={error.get('msg')}")
        except:
            print(f"  [ERROR] {response.text[:200]}")
except Exception as e:
    print(f"  [ERROR] {e}")

print("\n" + "=" * 70)
print("对比结果:")
print("  - 如果方式 1 成功，说明应该用 params")
print("  - 如果方式 2 成功，说明应该用 data")
print("  - 周末市场关闭，两种方式可能都返回 'Trading is currently suspended'")
print("=" * 70)
