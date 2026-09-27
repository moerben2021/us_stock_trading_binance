"""测试 Binance 下单 API 签名（参考官方实现）"""
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
print("Binance 股票下单 API 测试")
print("=" * 70)

# 测试 1: 先测试服务器时间
print("\n[测试 1] 获取 Binance 服务器时间")
print("-" * 70)
try:
    response = requests.get("https://api.binance.com/api/v3/time",
                           proxies={"http": "http://127.0.0.1:7990", "https": "http://127.0.0.1:7990"})
    server_time = response.json()["serverTime"]
    local_time = int(time.time() * 1000)
    time_diff = abs(server_time - local_time)

    print(f"服务器时间: {server_time}")
    print(f"本地时间: {local_time}")
    print(f"时间差: {time_diff} ms")

    if time_diff > 5000:
        print("  [WARNING] 时间差超过 5000ms，可能导致签名失败！")
    else:
        print("  [OK] 时间同步正常")
except Exception as e:
    print(f"  [ERROR] {e}")

# 测试 2: 测试账户余额查询（需要签名）
print("\n[测试 2] 查询资金账户余额（测试签名）")
print("-" * 70)

endpoint = "/sapi/v1/asset/get-funding-asset"
base_url = "https://api.binance.com"

# 构造参数
params = {
    "timestamp": int(time.time() * 1000)
}

# 生成签名（按字母顺序）
query_string = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
signature = hmac.new(
    secret_key.encode("utf-8"),
    query_string.encode("utf-8"),
    hashlib.sha256
).hexdigest()

params["signature"] = signature

# 设置 headers
headers = {
    "X-MBX-APIKEY": api_key
}

print(f"请求参数: {query_string}")
print(f"签名: [REDACTED - {len(signature)} chars]")

try:
    response = requests.post(
        base_url + endpoint,
        params=params,
        headers=headers,
        proxies={"http": "http://127.0.0.1:7990", "https": "http://127.0.0.1:7990"},
        timeout=10
    )

    print(f"响应状态: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"  [SUCCESS] 查询成功，返回 {len(data)} 个资产")
        for item in data[:3]:  # 只显示前 3 个
            print(f"    {item.get('asset')}: {item.get('free')}")
    else:
        try:
            error = response.json()
            print(f"  [ERROR] code={error.get('code')}, msg={error.get('msg')}")
        except:
            print(f"  [ERROR] {response.text[:200]}")

except Exception as e:
    print(f"  [ERROR] {e}")

# 测试 3: 测试下单接口（实际不会下单，只测试签名）
print("\n[测试 3] 测试下单接口参数和签名")
print("-" * 70)

endpoint = "/sapi/v1/equity/order/place"

# 下单参数
params = {
    "symbol": "SPY",
    "side": "BUY",
    "orderType": "MARKET",
    "notional": 6.0,
    "timestamp": int(time.time() * 1000)
}

print(f"下单参数:")
for k, v in params.items():
    print(f"  {k}: {v} ({type(v).__name__})")

# 生成签名
query_string = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
signature = hmac.new(
    secret_key.encode("utf-8"),
    query_string.encode("utf-8"),
    hashlib.sha256
).hexdigest()

print(f"\nQuery String (sorted):")
print(f"  {query_string}")
print(f"\n签名: [REDACTED - {len(signature)} chars]")

print("\n注意:")
print("  - 周末市场关闭，实际下单会返回 'Trading is currently suspended'")
print("  - 如果返回签名错误，需要检查 API Key 和 Secret Key")

print("\n" + "=" * 70)
