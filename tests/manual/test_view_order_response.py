"""测试下单接口并查看完整响应"""
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from integrations.binance_client import BinanceClient
import yaml
import json

print("=" * 70)
print("Test Order API - View Full Response")
print("=" * 70)

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

print("\n[Test] Place Order - SPY $6")
print("-" * 70)

try:
    # 下单
    response = client.place_order(
        symbol="SPY",
        side="BUY",
        quantity=6.0
    )

    print("\n[SUCCESS] Order placed!")
    print("\nFull API Response:")
    print(json.dumps(response, indent=2, ensure_ascii=False))

except Exception as e:
    print(f"\n[ERROR] Order failed: {e}")
    print(f"\nException type: {type(e).__name__}")

    # 尝试解析错误信息
    error_str = str(e)
    if "code" in error_str and "msg" in error_str:
        print(f"\nError details: {error_str}")

print("\n" + "=" * 70)
print("Check logs/app.log for detailed API response")
print("=" * 70)
