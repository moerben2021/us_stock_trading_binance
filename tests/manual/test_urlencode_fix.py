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
    secret_key=secrets['binance']['secret_key'],
    proxies={
        "http": "http://127.0.0.1:7990",
        "https": "http://127.0.0.1:7990"
    }
)

print("=" * 70)
print("Test Fixed Signature Generation (using urlencode)")
print("=" * 70)

# Test 1: Query funding account balance (known working endpoint)
print("\n[Test 1] Query Funding Account Balance")
print("-" * 70)

try:
    balance = client.get_account_balance()
    print(f"SUCCESS: Query returned {len(balance)} assets")
    for asset, info in balance.items():
        if float(info.get('free', 0)) > 0:
            print(f"  {asset}: {info.get('free')}")
except Exception as e:
    print(f"FAILED: {e}")

# Test 2: Place order (critical test)
print("\n[Test 2] Place Stock Order - SPY")
print("-" * 70)

try:
    result = client.place_order(
        symbol="SPY",
        side="BUY",
        quantity=6.0
    )

    print(f"SUCCESS: Order placed!")
    print(f"  Order ID: {result.get('orderId')}")
    print(f"  Status: {result.get('status')}")

except Exception as e:
    error_msg = str(e)

    if "suspended" in error_msg.lower() or "closed" in error_msg.lower():
        print(f"SUCCESS: Signature verified! (Market currently closed)")
        print(f"  Error message: {error_msg}")
    elif "-1022" in error_msg or "Signature" in error_msg:
        print(f"FAILED: Still signature error")
        print(f"  Error message: {error_msg}")
    else:
        print(f"WARNING: Other error: {error_msg}")

print("\n" + "=" * 70)
print("Test Complete")
print("=" * 70)
