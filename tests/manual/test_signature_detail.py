"""详细测试签名生成过程

WARNING: 这是调试专用脚本，会打印签名和查询字符串等敏感信息。
仅用于本地开发调试，禁止在生产环境运行。调试完成后应删除此文件。
"""
import hmac
import hashlib
import time
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
print("详细分析签名生成过程")
print("=" * 70)

# 测试参数
params = {
    "symbol": "SPY",
    "side": "BUY",
    "orderType": "MARKET",
    "notional": 6.0,
    "timestamp": 1727357946000  # 固定时间戳便于调试
}

print("\n[步骤 1] 原始参数")
print("-" * 70)
for k, v in params.items():
    print(f"  {k} = {v} (type: {type(v).__name__})")

# 尝试不同的参数格式化方式
print("\n[步骤 2] 测试不同的 query string 构造方式")
print("-" * 70)

# 方式 A: 直接转换（float 保持小数点）
query_a = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
sig_a = hmac.new(secret_key.encode("utf-8"), query_a.encode("utf-8"), hashlib.sha256).hexdigest()
print(f"\n方式 A: 直接转换")
print(f"  Query: {query_a}")
print(f"  Signature: [REDACTED - {len(sig_a)} chars]")

# 方式 B: notional 转为整数（如果是整数值）
params_b = params.copy()
if params_b["notional"] == int(params_b["notional"]):
    params_b["notional"] = int(params_b["notional"])
query_b = "&".join([f"{k}={v}" for k, v in sorted(params_b.items())])
sig_b = hmac.new(secret_key.encode("utf-8"), query_b.encode("utf-8"), hashlib.sha256).hexdigest()
print(f"\n方式 B: notional 转为整数")
print(f"  Query: {query_b}")
print(f"  Signature: [REDACTED - {len(sig_b)} chars]")

# 方式 C: 所有值转为字符串
params_c = {k: str(v) for k, v in params.items()}
query_c = "&".join([f"{k}={v}" for k, v in sorted(params_c.items())])
sig_c = hmac.new(secret_key.encode("utf-8"), query_c.encode("utf-8"), hashlib.sha256).hexdigest()
print(f"\n方式 C: 所有值显式转为字符串")
print(f"  Query: {query_c}")
print(f"  Signature: [REDACTED - {len(sig_c)} chars]")

# 方式 D: 检查参数顺序是否必须按字母排序
params_d_list = [
    ("notional", 6.0),
    ("orderType", "MARKET"),
    ("side", "BUY"),
    ("symbol", "SPY"),
    ("timestamp", 1727357946000)
]
query_d = "&".join([f"{k}={v}" for k, v in params_d_list])
sig_d = hmac.new(secret_key.encode("utf-8"), query_d.encode("utf-8"), hashlib.sha256).hexdigest()
print(f"\n方式 D: 按字母顺序排列")
print(f"  Query: {query_d}")
print(f"  Signature: [REDACTED - {len(sig_d)} chars]")

print("\n" + "=" * 70)
print("结论:")
print("  - 如果签名相同，说明参数格式化方式不影响")
print("  - 如果签名不同，需要找到正确的格式化方式")
print("=" * 70)

# 检查 API Key 和 Secret 是否正确加载
print("\n[步骤 3] 验证密钥加载")
print("-" * 70)
print(f"  API Key 长度: {len(api_key)}")
print(f"  Secret Key 长度: {len(secret_key)}")
