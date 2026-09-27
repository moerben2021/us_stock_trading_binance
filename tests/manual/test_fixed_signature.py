"""测试修复后的签名生成"""
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from integrations.binance_client import BinanceClient
import yaml

# 加载配置
with open('system.yaml', 'r', encoding='utf-8') as f:
    system_config = yaml.safe_load(f)

with open('secrets/account1.key', 'r', encoding='utf-8') as f:
    secrets = yaml.safe_load(f)

# 创建客户端
client = BinanceClient(
    api_key=secrets['binance']['api_key'],
    secret_key=secrets['binance']['secret_key'],  # 修正字段名
    proxies={
        "http": "http://127.0.0.1:7990",
        "https": "http://127.0.0.1:7990"
    }
)

print("=" * 70)
print("测试修复后的签名生成（使用 urlencode）")
print("=" * 70)

# 测试 1: 查询资金账户余额（已知成功的端点）
print("\n[测试 1] 查询资金账户余额")
print("-" * 70)

try:
    balance = client.get_account_balance()
    print(f"✅ 查询成功，返回 {len(balance)} 个资产")
    for asset, info in balance.items():
        if float(info.get('free', 0)) > 0:
            print(f"  {asset}: {info.get('free')}")
except Exception as e:
    print(f"❌ 查询失败: {e}")

# 测试 2: 下单（关键测试）
print("\n[测试 2] 股票下单 - SPY")
print("-" * 70)

try:
    result = client.place_order(
        symbol="SPY",
        side="BUY",
        quantity=6.0  # 使用金额
    )

    print(f"✅ 下单成功!")
    print(f"  订单ID: {result.get('orderId')}")
    print(f"  状态: {result.get('status')}")

except Exception as e:
    error_msg = str(e)

    if "suspended" in error_msg.lower() or "closed" in error_msg.lower():
        print(f"✅ 签名验证通过！（市场当前关闭）")
        print(f"  错误信息: {error_msg}")
    elif "-1022" in error_msg or "Signature" in error_msg:
        print(f"❌ 仍然是签名错误")
        print(f"  错误信息: {error_msg}")
    else:
        print(f"⚠️  其他错误: {error_msg}")

print("\n" + "=" * 70)
print("测试完成")
print("=" * 70)
