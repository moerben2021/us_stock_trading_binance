"""测试使用整数格式的 notional 参数"""
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
print("测试使用整数格式的 notional 参数下单")
print("=" * 70)

endpoint = "/sapi/v1/equity/order/place"
base_url = "https://api.binance.com"

# 测试 1: notional 使用整数
print("\n[测试 1] notional = 6（整数）")
print("-" * 70)

params1 = {
    "symbol": "SPY",
    "side": "BUY",
    "orderType": "MARKET",
    "notional": 6,  # 整数格式
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

    print(f"响应状态: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"[SUCCESS] 下单成功!")
        print(f"  订单ID: {result.get('orderId')}")
        print(f"  状态: {result.get('status')}")
    else:
        error = response.json()
        error_code = error.get('code', 'N/A')
        error_msg = error.get('msg', 'N/A')
        print(f"[ERROR] code={error_code}, msg={error_msg}")

        if error_code == -1022:
            print("  ❌ 仍然是签名错误")
        elif "Trading is currently suspended" in error_msg:
            print("  ✅ 签名验证通过！（市场关闭导致交易暂停）")
        else:
            print(f"  ⚠️  其他错误（但可能不是签名问题）")

except Exception as e:
    print(f"[ERROR] {e}")

# 测试 2: notional 使用浮点数
print("\n[测试 2] notional = 6.0（浮点数）")
print("-" * 70)

params2 = {
    "symbol": "SPY",
    "side": "BUY",
    "orderType": "MARKET",
    "notional": 6.0,  # 浮点数格式
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

    print(f"响应状态: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"[SUCCESS] 下单成功!")
        print(f"  订单ID: {result.get('orderId')}")
        print(f"  状态: {result.get('status')}")
    else:
        error = response.json()
        error_code = error.get('code', 'N/A')
        error_msg = error.get('msg', 'N/A')
        print(f"[ERROR] code={error_code}, msg={error_msg}")

        if error_code == -1022:
            print("  ❌ 签名错误")
        elif "Trading is currently suspended" in error_msg:
            print("  ✅ 签名验证通过！（市场关闭导致交易暂停）")
        else:
            print(f"  ⚠️  其他错误（但可能不是签名问题）")

except Exception as e:
    print(f"[ERROR] {e}")

print("\n" + "=" * 70)
print("结论:")
print("  - 如果测试 1 返回 'Trading is currently suspended'，")
print("    说明应该使用整数格式的 notional")
print("  - 如果测试 2 返回 'Trading is currently suspended'，")
print("    说明应该使用浮点数格式的 notional")
print("=" * 70)
