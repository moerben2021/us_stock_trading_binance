"""测试使用 request body 进行签名"""
import hmac
import hashlib
import time
import requests
from pathlib import Path
import yaml
from urllib.parse import urlencode

# 加载密钥
secrets_file = Path("secrets/account1.key")
with open(secrets_file, "r") as f:
    secrets = yaml.safe_load(f)

binance_config = secrets.get("binance", {})
api_key = binance_config.get("api_key")
secret_key = binance_config.get("secret_key")

base_url = "https://api.binance.com"
endpoint = "/sapi/v1/equity/order/place"

headers = {
    "X-MBX-APIKEY": api_key,
    "Content-Type": "application/x-www-form-urlencoded"
}

proxies = {"http": "http://127.0.0.1:7990", "https": "http://127.0.0.1:7990"}

print("=" * 70)
print("测试不同的参数传递和签名方式")
print("=" * 70)

# 方法 1: params 在 query string，签名也在 query string
print("\n[方法 1] 参数和签名都在 query string")
print("-" * 70)

params1 = {
    "symbol": "SPY",
    "side": "BUY",
    "orderType": "MARKET",
    "notional": 6,
    "timestamp": int(time.time() * 1000)
}

query_string1 = urlencode(sorted(params1.items()))
signature1 = hmac.new(secret_key.encode("utf-8"), query_string1.encode("utf-8"), hashlib.sha256).hexdigest()
params1["signature"] = signature1

print(f"Query String: {query_string1}")

try:
    response1 = requests.post(
        base_url + endpoint,
        params=params1,
        headers={"X-MBX-APIKEY": api_key},
        proxies=proxies,
        timeout=10
    )
    print(f"状态: {response1.status_code}")
    if response1.status_code != 200:
        error = response1.json()
        print(f"错误: code={error.get('code')}, msg={error.get('msg')}")
except Exception as e:
    print(f"异常: {e}")

# 方法 2: params 在 request body，签名基于 body
print("\n[方法 2] 参数在 request body，签名基于 body")
print("-" * 70)

params2 = {
    "symbol": "SPY",
    "side": "BUY",
    "orderType": "MARKET",
    "notional": 6,
    "timestamp": int(time.time() * 1000)
}

# 生成 body string（排序）
body_string2 = urlencode(sorted(params2.items()))
signature2 = hmac.new(secret_key.encode("utf-8"), body_string2.encode("utf-8"), hashlib.sha256).hexdigest()

# 签名添加到 body
body_with_sig = body_string2 + f"&signature={signature2}"

print(f"Body: {body_string2}")

try:
    response2 = requests.post(
        base_url + endpoint,
        data=body_with_sig,
        headers=headers,
        proxies=proxies,
        timeout=10
    )
    print(f"状态: {response2.status_code}")
    if response2.status_code == 200:
        result = response2.json()
        print(f"✅ 成功! Order ID: {result.get('orderId')}")
    else:
        error = response2.json()
        print(f"错误: code={error.get('code')}, msg={error.get('msg')}")
        if "suspended" in error.get('msg', '').lower():
            print("✅ 签名验证通过！（市场关闭）")
except Exception as e:
    print(f"异常: {e}")

# 方法 3: params 在 body，签名在 query string
print("\n[方法 3] 参数在 body，签名在 query string")
print("-" * 70)

params3 = {
    "symbol": "SPY",
    "side": "BUY",
    "orderType": "MARKET",
    "notional": 6,
    "timestamp": int(time.time() * 1000)
}

body_string3 = urlencode(sorted(params3.items()))
signature3 = hmac.new(secret_key.encode("utf-8"), body_string3.encode("utf-8"), hashlib.sha256).hexdigest()

print(f"Body: {body_string3}")

try:
    response3 = requests.post(
        base_url + endpoint + f"?signature={signature3}",
        data=body_string3,
        headers=headers,
        proxies=proxies,
        timeout=10
    )
    print(f"状态: {response3.status_code}")
    if response3.status_code == 200:
        result = response3.json()
        print(f"✅ 成功! Order ID: {result.get('orderId')}")
    else:
        error = response3.json()
        print(f"错误: code={error.get('code')}, msg={error.get('msg')}")
        if "suspended" in error.get('msg', '').lower():
            print("✅ 签名验证通过！（市场关闭）")
except Exception as e:
    print(f"异常: {e}")

# 方法 4: 使用官方 SDK 推荐的方式 - 参数不排序
print("\n[方法 4] 参数按原始顺序（不排序）")
print("-" * 70)

params4_list = [
    ("symbol", "SPY"),
    ("side", "BUY"),
    ("orderType", "MARKET"),
    ("notional", 6),
    ("timestamp", int(time.time() * 1000))
]

query_string4 = urlencode(params4_list)
signature4 = hmac.new(secret_key.encode("utf-8"), query_string4.encode("utf-8"), hashlib.sha256).hexdigest()

params4_with_sig = params4_list + [("signature", signature4)]

print(f"Query String: {query_string4}")

try:
    response4 = requests.post(
        base_url + endpoint,
        params=params4_with_sig,
        headers={"X-MBX-APIKEY": api_key},
        proxies=proxies,
        timeout=10
    )
    print(f"状态: {response4.status_code}")
    if response4.status_code == 200:
        result = response4.json()
        print(f"✅ 成功! Order ID: {result.get('orderId')}")
    else:
        error = response4.json()
        print(f"错误: code={error.get('code')}, msg={error.get('msg')}")
        if "suspended" in error.get('msg', '').lower():
            print("✅ 签名验证通过！（市场关闭）")
except Exception as e:
    print(f"异常: {e}")

print("\n" + "=" * 70)
print("如果任何一个方法显示 '签名验证通过'，说明找到了正确的方式")
print("=" * 70)
