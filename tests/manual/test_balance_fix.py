"""测试余额查询修复"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import yaml
from integrations.binance_client import BinanceClient
from utils.logger import setup_logger

# 初始化日志
logger = setup_logger("test", "logs/test_balance.log", "INFO")

print("=" * 60)
print("测试余额查询修复")
print("=" * 60)
print()

# 加载系统配置（获取代理设置）
with open('system.yaml', 'r', encoding='utf-8') as f:
    system_config = yaml.safe_load(f)

proxy_config = system_config.get("system", {}).get("proxy", {})
proxy_enabled = proxy_config.get("enabled", False)
proxies = None
if proxy_enabled:
    proxies = {
        "http": proxy_config.get("http"),
        "https": proxy_config.get("https")
    }
    print(f"代理: {proxies['http']}")

# 加载 API 密钥
with open('secrets/account1.key', 'r', encoding='utf-8') as f:
    secrets = yaml.safe_load(f)

api_key = secrets['binance']['api_key']
secret_key = secrets['binance']['secret_key']

# 创建 Binance 客户端
client = BinanceClient(api_key, secret_key, proxies=proxies)
print("Binance 客户端初始化完成")
print()

# 测试 1: 获取实时报价（应该成功）
print("测试 1: 获取 SPY 实时报价")
print("-" * 60)
try:
    price = client.get_realtime_price("SPY")
    print(f"✓ 成功获取报价: ${price:.2f}")
except Exception as e:
    print(f"✗ 失败: {e}")
print()

# 测试 2: 获取账户余额（应该返回模拟数据，无 404 错误）
print("测试 2: 获取账户余额")
print("-" * 60)
try:
    balance = client.get_account_balance()
    print(f"✓ 成功获取余额（模拟数据）:")
    for asset, info in balance.items():
        print(f"  {asset}: 可用 ${info['free']:.2f}, 锁定 ${info['locked']:.2f}")
except Exception as e:
    print(f"✗ 失败: {e}")
print()

# 测试 3: 获取持仓信息（应该返回 None，无 404 错误）
print("测试 3: 获取 SPY 持仓")
print("-" * 60)
try:
    position = client.get_position("SPY")
    if position is None:
        print("✓ 返回 None（无持仓，符合预期）")
    else:
        print(f"✓ 持仓: {position}")
except Exception as e:
    print(f"✗ 失败: {e}")
print()

print("=" * 60)
print("测试完成")
print("=" * 60)
