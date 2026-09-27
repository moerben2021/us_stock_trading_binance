"""详细对比资金账户查询和下单接口的请求差异"""
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

base_url = "https://api.binance.com"
headers = {"X-MBX-APIKEY": api_key}
proxies = {"http": "http://127.0.0.1:7990", "https": "http://127.0.0.1:7990"}

print("=" * 70)
print("详细对比两个 API 请求")
print("=" * 70)

# 测试 1: 资金账户查询（已知成功）
print("\n[测试 1] 资金账户查询 - /sapi/v1/asset/get-funding-asset")
print("-" * 70)

endpoint1 = "/sapi/v1/asset/get-funding-asset"
params1 = {"timestamp": int(time.time() * 1000)}

query_string1 = "&".join([f"{k}={v}" for k, v in sorted(params1.items())])
signature1 = hmac.new(secret_key.encode("utf-8"), query_string1.encode("utf-8"), hashlib.sha256).hexdigest()
params1["signature"] = signature1

print(f"Endpoint: {endpoint1}")
print(f"Method: POST")
print(f"Query String: {query_string1}")
print(f"Signature: [REDACTED - {len(signature1)} chars]")
print(f"Full URL: {base_url}{endpoint1}?{query_string1}&signature=[REDACTED]")

try:
    response1 = requests.post(base_url + endpoint1, params=params1, headers=headers, proxies=proxies, timeout=10)
    print(f"Status: {response1.status_code}")

    if response1.status_code == 200:
        result = response1.json()
        print(f"Result: SUCCESS - {len(result)} assets")
    else:
        error = response1.json()
        print(f"Result: ERROR - code={error.get('code')}, msg={error.get('msg')}")
except Exception as e:
    print(f"Exception: {e}")

# 测试 2: 下单接口（已知失败）
print("\n[测试 2] 股票下单 - /sapi/v1/equity/order/place")
print("-" * 70)

endpoint2 = "/sapi/v1/equity/order/place"
params2 = {
    "symbol": "SPY",
    "side": "BUY",
    "orderType": "MARKET",
    "notional": 6,
    "timestamp": int(time.time() * 1000)
}

query_string2 = "&".join([f"{k}={v}" for k, v in sorted(params2.items())])
signature2 = hmac.new(secret_key.encode("utf-8"), query_string2.encode("utf-8"), hashlib.sha256).hexdigest()
params2["signature"] = signature2

print(f"Endpoint: {endpoint2}")
print(f"Method: POST")
print(f"Query String: {query_string2}")
print(f"Signature: [REDACTED - {len(signature2)} chars]")
print(f"Full URL: {base_url}{endpoint2}?{query_string2}&signature=[REDACTED]")

try:
    response2 = requests.post(base_url + endpoint2, params=params2, headers=headers, proxies=proxies, timeout=10)
    print(f"Status: {response2.status_code}")

    if response2.status_code == 200:
        result = response2.json()
        print(f"Result: SUCCESS - Order ID {result.get('orderId')}")
    else:
        error = response2.json()
        print(f"Result: ERROR - code={error.get('code')}, msg={error.get('msg')}")
except Exception as e:
    print(f"Exception: {e}")

# 测试 3: 尝试使用 data 而不是 params（request body）
print("\n[测试 3] 股票下单 - 使用 request body")
print("-" * 70)

params3 = {
    "symbol": "SPY",
    "side": "BUY",
    "orderType": "MARKET",
    "notional": 6,
    "timestamp": int(time.time() * 1000)
}

query_string3 = "&".join([f"{k}={v}" for k, v in sorted(params3.items())])
signature3 = hmac.new(secret_key.encode("utf-8"), query_string3.encode("utf-8"), hashlib.sha256).hexdigest()
params3["signature"] = signature3

print(f"Query String: {query_string3}")
print(f"Signature: [REDACTED - {len(signature3)} chars]")

try:
    response3 = requests.post(base_url + endpoint2, data=params3, headers=headers, proxies=proxies, timeout=10)
    print(f"Status: {response3.status_code}")

    if response3.status_code == 200:
        result = response3.json()
        print(f"Result: SUCCESS - Order ID {result.get('orderId')}")
    else:
        error = response3.json()
        print(f"Result: ERROR - code={error.get('code')}, msg={error.get('msg')}")
except Exception as e:
    print(f"Exception: {e}")

print("\n" + "=" * 70)
print("分析:")
print("  - 测试 1 应该成功（已验证）")
print("  - 测试 2 和 3 对比 params vs data")
print("  - 关键是找出下单接口为什么签名验证失败")
print("=" * 70)
