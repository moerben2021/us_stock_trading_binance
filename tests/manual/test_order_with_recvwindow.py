"""测试添加 recvWindow 参数"""
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
print("测试添加 recvWindow 参数")
print("=" * 70)

endpoint = "/sapi/v1/equity/order/place"
base_url = "https://api.binance.com"

# 测试 1: 不带 recvWindow
print("\n[测试 1] 不带 recvWindow 参数")
print("-" * 70)

params1 = {
    "symbol": "SPY",
    "side": "BUY",
    "orderType": "MARKET",
    "notional": 6,
    "timestamp": int(time.time() * 1000)
}

query_string1 = "&".join([f"{k}={v}" for k, v in sorted(params1.items())])
signature1 = hmac.new(
    secret_key.encode("utf-8"),
    query_string1.encode("utf-8"),
    hashlib.sha256
).hexdigest()

params1["signature"] = signature1

headers = {"X-MBX-APIKEY": api_key}
proxies = {"http": "http://127.0.0.1:7990", "https": "http://127.0.0.1:7990"}

print(f"Query String: {query_string1}")

try:
    response = requests.post(
        base_url + endpoint,
        params=params1,
        headers=headers,
        proxies=proxies,
        timeout=10
    )

    print(f"Response Status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"[SUCCESS] Order ID: {result.get('orderId')}")
    else:
        error = response.json()
        print(f"[ERROR] code={error.get('code')}, msg={error.get('msg')}")

except Exception as e:
    print(f"[ERROR] {e}")

# 测试 2: 带 recvWindow=5000
print("\n[测试 2] 带 recvWindow=5000")
print("-" * 70)

params2 = {
    "symbol": "SPY",
    "side": "BUY",
    "orderType": "MARKET",
    "notional": 6,
    "recvWindow": 5000,
    "timestamp": int(time.time() * 1000)
}

query_string2 = "&".join([f"{k}={v}" for k, v in sorted(params2.items())])
signature2 = hmac.new(
    secret_key.encode("utf-8"),
    query_string2.encode("utf-8"),
    hashlib.sha256
).hexdigest()

params2["signature"] = signature2

print(f"Query String: {query_string2}")

try:
    response = requests.post(
        base_url + endpoint,
        params=params2,
        headers=headers,
        proxies=proxies,
        timeout=10
    )

    print(f"Response Status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"[SUCCESS] Order ID: {result.get('orderId')}")
    else:
        error = response.json()
        print(f"[ERROR] code={error.get('code')}, msg={error.get('msg')}")

except Exception as e:
    print(f"[ERROR] {e}")

# 测试 3: 对比资金账户查询（这个是成功的）
print("\n[测试 3] 资金账户查询（用于对比）")
print("-" * 70)

endpoint_funding = "/sapi/v1/asset/get-funding-asset"

params3 = {
    "timestamp": int(time.time() * 1000)
}

query_string3 = "&".join([f"{k}={v}" for k, v in sorted(params3.items())])
signature3 = hmac.new(
    secret_key.encode("utf-8"),
    query_string3.encode("utf-8"),
    hashlib.sha256
).hexdigest()

params3["signature"] = signature3

print(f"Query String: {query_string3}")

try:
    response = requests.post(
        base_url + endpoint_funding,
        params=params3,
        headers=headers,
        proxies=proxies,
        timeout=10
    )

    print(f"Response Status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"[SUCCESS] Returned {len(result)} assets")
        for item in result:
            print(f"  {item.get('asset')}: {item.get('free')}")
    else:
        error = response.json()
        print(f"[ERROR] code={error.get('code')}, msg={error.get('msg')}")

except Exception as e:
    print(f"[ERROR] {e}")

print("\n" + "=" * 70)
