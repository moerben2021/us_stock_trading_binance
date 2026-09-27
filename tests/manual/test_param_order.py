"""测试参数不排序的签名方式"""
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

binance_config = secrets.get("binance", )
api_key = binance_config.get("api_key")
secret_key = binance_config.get("secret_key")

base_url = "https://api.binance.com"
endpoint = "/sapi/v1/equity/order/place"
headers = {"X-MBX-APIKEY": api_key}
proxies = {"http": "http://127.0.0.1:7990", "https": "http://127.0.0.1:7990"}

print("=" * 70)
print("测试：参数不排序 vs 排序")
print("=" * 70)

# 测试 1: 参数按添加顺序（不排序）
print("\n[测试 1] 参数按原始顺序（不排序）")
print("-" * 70)

timestamp1 = int(time.time() * 1000)

# 按照文档中的参数顺序
param_pairs1 = [
    ("symbol", "SPY"),
    ("side", "BUY"),
    ("orderType", "MARKET"),
    ("notional", "6"),  # 注意：改为字符串
    ("timestamp", str(timestamp1))
]

query_string1 = "&".join([f"{k}={v}" for k, v in param_pairs1])
signature1 = hmac.new(secret_key.encode("utf-8"), query_string1.encode("utf-8"), hashlib.sha256).hexdigest()

# 构造完整参数（包含签名）
full_params1 = dict(param_pairs1)
full_params1["signature"] = signature1

print(f"Query String: {query_string1}")
print(f"Signature: [REDACTED - {len(signature1)} chars]")

try:
    response1 = requests.post(
        base_url + endpoint,
        params=full_params1,
        headers=headers,
        proxies=proxies,
        timeout=10
    )

    print(f"状态码: {response1.status_code}")

    if response1.status_code == 200:
        result = response1.json()
        print(f"✅ [SUCCESS] 下单成功!")
        print(f"   订单ID: {result.get('orderId')}")
    else:
        error = response1.json()
        error_code = error.get('code', 'N/A')
        error_msg = error.get('msg', 'N/A')
        print(f"❌ [ERROR] code={error_code}, msg={error_msg}")

        if "suspended" in error_msg.lower() or "closed" in error_msg.lower():
            print("   ✅ 签名验证通过！（市场当前关闭）")
        elif error_code == -1022:
            print("   ❌ 仍然是签名错误")

except Exception as e:
    print(f"异常: {e}")

# 测试 2: 参数按字母排序（当前实现）
print("\n[测试 2] 参数按字母排序")
print("-" * 70)

timestamp2 = int(time.time() * 1000)

params2 = {
    "symbol": "SPY",
    "side": "BUY",
    "orderType": "MARKET",
    "notional": "6",
    "timestamp": str(timestamp2)
}

# 按字母排序
query_string2 = "&".join([f"{k}={v}" for k, v in sorted(params2.items())])
signature2 = hmac.new(secret_key.encode("utf-8"), query_string2.encode("utf-8"), hashlib.sha256).hexdigest()

params2["signature"] = signature2

print(f"Query String: {query_string2}")
print(f"Signature: [REDACTED - {len(signature2)} chars]")

try:
    response2 = requests.post(
        base_url + endpoint,
        params=params2,
        headers=headers,
        proxies=proxies,
        timeout=10
    )

    print(f"状态码: {response2.status_code}")

    if response2.status_code == 200:
        result = response2.json()
        print(f"✅ [SUCCESS] 下单成功!")
        print(f"   订单ID: {result.get('orderId')}")
    else:
        error = response2.json()
        error_code = error.get('code', 'N/A')
        error_msg = error.get('msg', 'N/A')
        print(f"❌ [ERROR] code={error_code}, msg={error_msg}")

        if "suspended" in error_msg.lower() or "closed" in error_msg.lower():
            print("   ✅ 签名验证通过！（市场当前关闭）")
        elif error_code == -1022:
            print("   ❌ 仍然是签名错误")

except Exception as e:
    print(f"异常: {e}")

print("\n" + "=" * 70)
print("结论:")
print("  如果测试 1 通过，说明参数不应该排序")
print("  如果测试 2 通过，说明参数需要排序")
print("=" * 70)
