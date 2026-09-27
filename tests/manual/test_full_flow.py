"""完整测试：模拟 main.py 启动并执行策略"""
import sys
import os
from pathlib import Path

# 添加项目根目录到 sys.path
sys.path.insert(0, str(Path(__file__).parent))

# ============================================================
# 关键：在导入任何模块之前，先设置环境变量代理
# ============================================================
import yaml

system_yaml_path = Path(__file__).parent / "system.yaml"
if system_yaml_path.exists():
    with open(system_yaml_path, "r", encoding="utf-8") as f:
        _system_config = yaml.safe_load(f)

    _proxy_config = _system_config.get("system", {}).get("proxy", {})
    _proxy_enabled = _proxy_config.get("enabled", False)

    if _proxy_enabled:
        _http_proxy = _proxy_config.get("http")
        _https_proxy = _proxy_config.get("https")

        os.environ["HTTP_PROXY"] = _http_proxy
        os.environ["HTTPS_PROXY"] = _https_proxy
        os.environ["http_proxy"] = _http_proxy
        os.environ["https_proxy"] = _https_proxy

        print(f"[EARLY INIT] 代理环境变量已设置: {_http_proxy}")
        print(f"[VERIFY] HTTP_PROXY = {os.environ.get('HTTP_PROXY')}")
        print(f"[VERIFY] HTTPS_PROXY = {os.environ.get('HTTPS_PROXY')}")

# 现在可以导入其他模块
from config.loader import ConfigLoader
from storage.database import Database
from integrations.yfinance_client import YFinanceClient
from integrations.binance_client import BinanceClient
from integrations.market_data_service import MarketDataService
from core.strategy_engine import StrategyEngine
from core.trade_executor import TradeExecutor
from integrations.wecom_notifier import WeComNotifier

print("\n" + "=" * 70)
print("完整流程测试")
print("=" * 70)

# 初始化组件
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

database = Database("data/trading.db")
database.init_db()

yfinance_client = YFinanceClient()
accounts = config_loader.load_account_configs()
account = accounts[0]

api_key = account.get("account", {}).get("api_key")
secret_key = account.get("account", {}).get("secret_key")

binance_client = BinanceClient(api_key, secret_key, proxies)
market_data_service = MarketDataService(yfinance_client, binance_client)
wecom_notifier = WeComNotifier()
trade_executor = TradeExecutor(binance_client, database, wecom_notifier, system_config)
strategy_engine = StrategyEngine(market_data_service, binance_client, database, trade_executor)

print("[OK] 所有组件初始化完成")

# 执行 DCA SPY 策略
print("\n" + "=" * 70)
print("执行 DCA SPY 策略")
print("=" * 70)

strategy_instance = None
for strategy in account.get("strategies", []):
    if strategy.get("id") == "dca_spy_monthly":
        strategy_instance = strategy
        break

if strategy_instance:
    print(f"\n策略: {strategy_instance.get('id')}")
    print(f"类型: {strategy_instance.get('type')}")
    print(f"标的: {strategy_instance.get('symbol')}")
    print(f"金额: ${strategy_instance.get('config', {}).get('base_amount')}")

    print("\n开始执行...")
    print("-" * 70)

    try:
        result = strategy_engine.execute_strategy(account, strategy_instance)
        print("\n" + "=" * 70)
        print("[SUCCESS] 策略执行完成")
        print("=" * 70)
        print(f"结果: {result}")
    except Exception as e:
        print("\n" + "=" * 70)
        print("[FAILED] 策略执行失败")
        print("=" * 70)
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
else:
    print("[ERROR] 未找到策略")
