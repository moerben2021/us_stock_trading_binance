"""测试账户余额和持仓查询"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import yaml
from integrations.binance_client import BinanceClient
from utils.logger import setup_logger

# 初始化日志
logger = setup_logger("test", "logs/test_account.log", "INFO")

print("=" * 60)
print("测试账户余额和持仓查询")
print("=" * 60)
print()

# 加载系统配置
with open('system.yaml', 'r', encoding='utf-8') as f:
    system_config = yaml.safe_load(f)

proxy_config = system_config.get("system", {}).get("proxy", {})
proxies = None
if proxy_config.get("enabled", False):
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

# 创建客户端
client = BinanceClient(api_key, secret_key, proxies=proxies)
print("Binance 客户端初始化完成")
print()

# 测试 1: 获取账户余额
print("测试 1: 获取账户余额")
print("-" * 60)
try:
    balance = client.get_account_balance()
    print(f"[SUCCESS] 获取余额成功，共 {len(balance)} 个资产:")

    # 分类显示：现金和股票
    cash_assets = []
    stock_assets = []

    for asset, info in balance.items():
        total = info['free'] + info['locked']
        if asset in ['USD', 'USDT', 'BUSD']:
            cash_assets.append((asset, info))
        else:
            stock_assets.append((asset, info))

    if cash_assets:
        print("\n现金资产:")
        for asset, info in cash_assets:
            total = info['free'] + info['locked']
            print(f"  {asset}: ${total:.2f} (可用: ${info['free']:.2f}, 锁定: ${info['locked']:.2f})")

    if stock_assets:
        print("\n股票持仓:")
        for asset, info in stock_assets:
            total = info['free'] + info['locked']
            print(f"  {asset}: {total:.4f} 股 (可用: {info['free']:.4f}, 锁定: {info['locked']:.4f})")

except Exception as e:
    print(f"[ERROR] 失败: {e}")
print()

# 测试 2: 查询特定股票持仓
print("测试 2: 查询 SPY 持仓")
print("-" * 60)
try:
    position = client.get_position("SPY")
    if position:
        print(f"[SUCCESS] 持仓信息:")
        print(f"  股票: {position['symbol']}")
        print(f"  数量: {position['quantity']:.4f} 股")
        print(f"  平均成本: ${position['avg_cost']:.2f} (待实现)")
    else:
        print("[INFO] 无持仓")
except Exception as e:
    print(f"[ERROR] 失败: {e}")
print()

# 测试 3: 查询另一个股票
print("测试 3: 查询 QQQ 持仓")
print("-" * 60)
try:
    position = client.get_position("QQQ")
    if position:
        print(f"[SUCCESS] 持仓信息:")
        print(f"  股票: {position['symbol']}")
        print(f"  数量: {position['quantity']:.4f} 股")
        print(f"  平均成本: ${position['avg_cost']:.2f} (待实现)")
    else:
        print("[INFO] 无持仓")
except Exception as e:
    print(f"[ERROR] 失败: {e}")
print()

print("=" * 60)
print("测试完成")
print("=" * 60)
