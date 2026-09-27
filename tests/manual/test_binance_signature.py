"""测试 Binance API 签名生成"""
import hmac
import hashlib
import time
from pathlib import Path
import yaml

# 加载密钥
secrets_file = Path("secrets/account1.key")
with open(secrets_file, "r") as f:
    secrets = yaml.safe_load(f)

# 密钥文件使用 binance 嵌套结构
binance_config = secrets.get("binance", {})
api_key = binance_config.get("api_key")
secret_key = binance_config.get("secret_key")

print("=" * 70)
print("Binance API 签名测试")
print("=" * 70)

# 测试参数（与下单请求相同）
params = {
    "symbol": "SPY",
    "side": "BUY",
    "orderType": "MARKET",
    "notional": 6.0,
    "timestamp": int(time.time() * 1000)
}

print(f"\n原始参数:")
for k, v in params.items():
    print(f"  {k}: {v}")

# 按字母顺序排列
sorted_params = sorted(params.items())
print(f"\n排序后参数:")
for k, v in sorted_params:
    print(f"  {k}: {v}")

# 生成 query string
query_string = "&".join([f"{k}={v}" for k, v in sorted_params])
print(f"\nQuery String:")
print(f"  {query_string}")

# 生成签名
signature = hmac.new(
    secret_key.encode("utf-8"),
    query_string.encode("utf-8"),
    hashlib.sha256
).hexdigest()

print(f"\n签名:")
print(f"  [REDACTED - {len(signature)} chars]")

# 构造完整 URL
url = f"https://api.binance.com/sapi/v1/equity/order/place?{query_string}&signature=[REDACTED]"
print(f"\n完整 URL:")
print(f"  {url}")

print(f"\nHeaders:")
print(f"  X-MBX-APIKEY: {api_key[:10]}...")

print("\n" + "=" * 70)
print("提示:")
print("  1. 检查 secret_key 是否正确")
print("  2. 检查参数类型（notional 应该是数字，不是字符串）")
print("  3. 检查时间戳是否在有效范围内（±5000ms）")
print("=" * 70)
