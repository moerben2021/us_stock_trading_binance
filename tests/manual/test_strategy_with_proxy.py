"""手动触发策略测试 yFinance 代理"""
import sys
import os
from pathlib import Path

# 添加项目根目录到 sys.path
sys.path.insert(0, str(Path(__file__).parent))

from config.loader import ConfigLoader
from storage.database import Database
from integrations.yfinance_client import YFinanceClient
from integrations.binance_client import BinanceClient
from integrations.market_data_service import MarketDataService
from core.strategy_engine import StrategyEngine
from core.trade_executor import TradeExecutor
from integrations.wecom_notifier import WeComNotifier

print("=" * 70)
print("手动触发策略测试")
print("=" * 70)

# 1. 加载配置并设置环境变量（模拟 main.py）
print("\n[步骤 1] 加载配置并设置环境变量")
print("-" * 70)
config_loader = ConfigLoader()
system_config = config_loader.load_system_config()

proxy_config = system_config.get("system", {}).get("proxy", {})
proxy_enabled = proxy_config.get("enabled", False)

proxies = None
if proxy_enabled:
    proxies = {
        "http": proxy_config.get("http"),
        "https": proxy_config.get("https")
    }
    os.environ["HTTP_PROXY"] = proxies["http"]
    os.environ["HTTPS_PROXY"] = proxies["https"]
    os.environ["http_proxy"] = proxies["http"]
    os.environ["https_proxy"] = proxies["https"]
    print(f"已设置环境变量: {proxies['http']}")

print(f"环境变量验证:")
print(f"  HTTP_PROXY: {os.environ.get('HTTP_PROXY')}")
print(f"  HTTPS_PROXY: {os.environ.get('HTTPS_PROXY')}")

# 2. 初始化组件
print("\n[步骤 2] 初始化组件")
print("-" * 70)

database = Database("data/trading.db")
database.init_db()
print("数据库初始化完成")

yfinance_client = YFinanceClient()
print("yFinance 客户端初始化完成")

accounts = config_loader.load_account_configs()
account = accounts[0]
account_name = account.get("account", {}).get("name")

api_key = account.get("account", {}).get("api_key")
secret_key = account.get("account", {}).get("secret_key")

binance_client = BinanceClient(api_key, secret_key, proxies)
print(f"Binance 客户端初始化完成: {account_name}")

market_data_service = MarketDataService(yfinance_client, binance_client)
print("市场数据服务初始化完成")

wecom_notifier = WeComNotifier()
trade_executor = TradeExecutor(binance_client, database, wecom_notifier)
strategy_engine = StrategyEngine(market_data_service, binance_client, database, trade_executor)
print("策略引擎初始化完成")

# 3. 执行 DCA SPY 策略
print("\n[步骤 3] 执行 DCA SPY 策略")
print("-" * 70)

strategy_instance = None
for strategy in account.get("strategies", []):
    if strategy.get("id") == "dca_spy_monthly":
        strategy_instance = strategy
        break

if strategy_instance:
    print(f"策略配置: {strategy_instance.get('id')}")
    print(f"  类型: {strategy_instance.get('type')}")
    print(f"  标的: {strategy_instance.get('symbol')}")
    print(f"  金额: ${strategy_instance.get('config', {}).get('base_amount')}")

    print("\n开始执行策略...")
    try:
        result = strategy_engine.execute_strategy(account, strategy_instance)
        print(f"\n[SUCCESS] 策略执行完成")
        print(f"结果: {result}")
    except Exception as e:
        print(f"\n[FAILED] 策略执行失败: {e}")
        import traceback
        traceback.print_exc()
else:
    print("[ERROR] 未找到 dca_spy_monthly 策略")

print("\n" + "=" * 70)
print("测试完成")
print("=" * 70)
