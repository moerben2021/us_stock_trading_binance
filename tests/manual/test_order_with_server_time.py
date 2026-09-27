"""使用 Binance 服务器时间测试下单"""
import hmac
import hashlib
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
print("使用 Binance 服务器时间测试下单")
print("=" * 70)

# 步骤 1: 获取 Binance 服务器时间
print("\n[步骤 1] 获取 Binance 服务器时间")
print("-" * 70)

try:
    time_response = requests.get(
        base_url + "/api/v3/time",
        proxies=proxies,
        timeout=10
    )

    if time_response.status_code == 200:
        server_time = time_response.json().get("serverTime")
        print(f"服务器时间: {server_time}")
    else:
        print(f"[ERROR] 无法获取服务器时间: {time_response.status_code}")
        exit(1)

except Exception as e:
    print(f"[ERROR] {e}")
    exit(1)

# 步骤 2: 使用服务器时间下单
print("\n[步骤 2] 使用服务器时间下单")
print("-" * 70)

endpoint = "/sapi/v1/equity/order/place"

params = {
    "symbol": "SPY",
    "side": "BUY",
    "orderType": "MARKET",
    "notional": 6,
    "timestamp": server_time  # 使用服务器时间
}

# 生成签名
query_string = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
signature = hmac.new(
    secret_key.encode("utf-8"),
    query_string.encode("utf-8"),
    hashlib.sha256
).hexdigest()

params["signature"] = signature

print(f"Query String: {query_string}")
print(f"Signature: [REDACTED - {len(signature)} chars]")

try:
    response = requests.post(
        base_url + endpoint,
        params=params,
        headers=headers,
        proxies=proxies,
        timeout=10
    )

    print(f"\n响应状态: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"\n✅ [SUCCESS] 下单成功!")
        print(f"订单ID: {result.get('orderId')}")
        print(f"状态: {result.get('status')}")
        print(f"\n完整响应:")
        print(result)
    else:
        error = response.json()
        error_code = error.get('code', 'N/A')
        error_msg = error.get('msg', 'N/A')

        print(f"\n❌ [ERROR] code={error_code}, msg={error_msg}")

        if error_code == -1022:
            print("\n仍然是签名错误。可能原因:")
            print("  1. API Key 没有股票交易权限")
            print("  2. 参数格式或顺序问题")
            print("  3. 签名算法实现细节差异")
        elif "suspended" in error_msg.lower():
            print("\n✅ 签名验证通过！（但市场当前关闭）")

except Exception as e:
    print(f"\n[ERROR] {e}")

print("\n" + "=" * 70)
