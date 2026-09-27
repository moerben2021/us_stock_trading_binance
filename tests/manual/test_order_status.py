"""测试修复后的签名 - 详细输出版本"""
import sys
import os
from pathlib import Path
import json

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
print("Test Order Placement with Fixed Signature")
print("=" * 70)

# Test: Place order
print("\n[Test] Place Stock Order - SPY $6")
print("-" * 70)

try:
    result = client.place_order(
        symbol="SPY",
        side="BUY",
        quantity=6.0
    )

    print(f"Order placement SUCCESS!")
    print(f"Full response:")
    print(json.dumps(result, indent=2, ensure_ascii=False))

except Exception as e:
    print(f"Order placement FAILED")
    print(f"Exception type: {type(e).__name__}")
    print(f"Exception message: {str(e)}")

    # 解析错误信息
    error_msg = str(e)

    # 检查是否是签名错误
    if "-1022" in error_msg or "Signature" in error_msg:
        print("\n[RESULT] Still signature error - fix did not work")
    # 检查是否是市场关闭
    elif "suspended" in error_msg.lower() or "closed" in error_msg.lower() or "not open" in error_msg.lower():
        print("\n[RESULT] Signature VERIFIED! Market is closed (expected on weekend)")
    # 其他错误
    else:
        print(f"\n[RESULT] Other error (possibly signature passed): {error_msg}")

print("\n" + "=" * 70)
