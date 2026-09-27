"""完整集成测试 - 模拟主程序流程"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import time
from datetime import datetime
import pytz
from config.loader import ConfigLoader
from core.scheduler import Scheduler
from core.strategy_engine import StrategyEngine
from integrations.market_data_service import MarketDataService
from integrations.yfinance_client import YFinanceClient
from integrations.binance_client import BinanceClient
from integrations.wecom_notifier import WeComNotifier
from storage.database import Database
from core.trade_executor import TradeExecutor
from utils.logger import setup_logger

print("=" * 60)
print("完整集成测试")
print("=" * 60)
print()

# 初始化日志
logger = setup_logger("test", "logs/test_integration.log", "DEBUG")
logger.info("=" * 60)
logger.info("集成测试开始")
logger.info("=" * 60)

# 加载配置
config_loader = ConfigLoader()
system_config = config_loader.load_system_config()
accounts = config_loader.load_account_configs()

# 读取代理配置
proxy_config = system_config.get("system", {}).get("proxy", {})
proxy_enabled = proxy_config.get("enabled", False)
proxies = None
if proxy_enabled:
    proxies = {
        "http": proxy_config.get("http"),
        "https": proxy_config.get("https")
    }
    print(f"代理已启用: {proxies['http']}")
else:
    print("代理未启用（直连）")

# 初始化数据库
database = Database("data/trading.db")
database.init_db()
print("数据库初始化完成")

# 初始化外部集成
yfinance_client = YFinanceClient()
wecom_notifier = WeComNotifier()
print("外部集成初始化完成")

# 初始化 Binance 客户端
first_account = accounts[0]
account_name = first_account.get("account", {}).get("name")
api_key = first_account.get("binance", {}).get("api_key")
secret_key = first_account.get("binance", {}).get("secret_key")

binance_client = BinanceClient(api_key, secret_key, proxies=proxies)
print(f"Binance 客户端初始化完成: {account_name}")

# 初始化核心模块
market_data_service = MarketDataService(yfinance_client, binance_client)
trade_executor = TradeExecutor(binance_client, database, wecom_notifier, system_config)
strategy_engine = StrategyEngine(market_data_service, binance_client, database, trade_executor)
print("核心模块初始化完成")

# 获取当前美东时间
et = pytz.timezone('America/New_York')
now_et = datetime.now(et)
print(f"\n当前美东时间: {now_et.strftime('%Y-%m-%d %H:%M:%S %Z')}")

# 显示策略配置
print(f"\n账户: {account_name}")
strategies = first_account.get("strategies", [])
active_strategies = [s for s in strategies if s.get("status") == "active"]
print(f"活跃策略数量: {len(active_strategies)}")

for strategy in active_strategies[:3]:  # 只显示前3个
    sid = strategy.get("id")
    schedule = strategy.get("schedule")
    symbol = strategy.get("symbol")
    print(f"  - {sid}: {symbol}, schedule={schedule}")

print()

# 初始化并启动调度器
scheduler = Scheduler(config_loader, strategy_engine, system_config)
print("调度器初始化完成")
print()
print("=" * 60)
print("启动调度器...")
print("=" * 60)
print()

try:
    # 启动调度器（这会阻塞并等待 KeyboardInterrupt）
    scheduler.start(accounts)
except KeyboardInterrupt:
    print("\n收到中断信号")
finally:
    database.close()
    print("数据库已关闭")
    print("测试结束")
