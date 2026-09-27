"""对比分析：修复前后的签名生成差异

WARNING: 这是仅用于本地开发的对比分析脚本。
- 使用测试密钥，不要使用真实 API 密钥
- 会打印签名和查询字符串用于调试
- 仅供学习和验证签名算法差异
- 调试完成后应删除此文件
"""
import hmac
import hashlib
from urllib.parse import urlencode

# 测试参数
params = {
    "symbol": "SPY",
    "side": "BUY",
    "orderType": "MARKET",
    "notional": 6,
    "timestamp": 1727357946000
}

# 仅用于测试的虚拟密钥（不要使用真实密钥！）
secret_key = "test_secret_key"

print("=" * 80)
print("签名生成方式对比")
print("=" * 80)

# 方式 1: 修复前（手动拼接，按字母排序）
print("\n[方式 1] 修复前 - 手动拼接 + 排序")
print("-" * 80)
query_old = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
sig_old = hmac.new(secret_key.encode("utf-8"), query_old.encode("utf-8"), hashlib.sha256).hexdigest()
print(f"Query String: {query_old}")
print(f"Signature: [REDACTED - {len(sig_old)} chars]")

# 方式 2: 修复后（使用 urlencode）
print("\n[方式 2] 修复后 - urlencode")
print("-" * 80)
query_new = urlencode(params)
sig_new = hmac.new(secret_key.encode("utf-8"), query_new.encode("utf-8"), hashlib.sha256).hexdigest()
print(f"Query String: {query_new}")
print(f"Signature: [REDACTED - {len(sig_new)} chars]")

# 方式 3: 成功项目的方式（urlencode，tqqq-bot 的实现）
print("\n[方式 3] 成功项目 (tqqq-bot) - urlencode")
print("-" * 80)
print(f"Query String: {query_new}")
print(f"Signature: [REDACTED - {len(sig_new)} chars]")
print("（与方式 2 相同）")

# 分析差异
print("\n" + "=" * 80)
print("差异分析")
print("=" * 80)

if query_old == query_new:
    print("Query String: 相同")
else:
    print("Query String: 不同")
    print(f"  修复前: {query_old}")
    print(f"  修复后: {query_new}")

if sig_old == sig_new:
    print("Signature: 相同")
else:
    print("Signature: 不同")
    print(f"  修复前: [REDACTED - {len(sig_old)} chars]")
    print(f"  修复后: [REDACTED - {len(sig_new)} chars]")

print("\n" + "=" * 80)
print("结论")
print("=" * 80)
print("urlencode() 的特点:")
print("1. 自动对参数值进行 URL 编码（百分号编码）")
print("2. 参数按照字典顺序排列")
print("3. 处理特殊字符（如空格 -> %20）")
print("\n修复说明:")
print("- 成功项目使用 urlencode() 生成签名")
print("- 我们的代码已修改为使用相同的方式")
print("- 这应该能解决 Binance API 的签名验证问题")
print("=" * 80)
