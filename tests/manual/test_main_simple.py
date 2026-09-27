"""简化主程序测试 - 只测试调度器启动"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import yaml
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
print("简化主程序测试")
print("=" * 60)

logger = setup_logger("main", "logs/test_main_simple.log", "DEBUG")
logger.info("=" * 60)
logger.info("简化测试开始")
logger.info("=" * 60)

try:
    # 加载配置
    config_loader = ConfigLoader()
    system_config = config_loader.load_system_config()
    accounts = config_loader.load_account_configs()
    logger.info(f"已加载 {len(accounts)} 个账户配置")

    # 初始化组件
    proxy_config = system_config.get("system", {}).get("proxy", {})
    proxies = None
    if proxy_config.get("enabled", False):
        proxies = {"http": proxy_config.get("http"), "https": proxy_config.get("https")}

    database = Database("data/trading.db")
    database.init_db()
    logger.info("数据库初始化完成")

    yfinance_client = YFinanceClient()
    wecom_notifier = WeComNotifier()

    first_account = accounts[0]
    api_key = first_account.get("binance", {}).get("api_key")
    secret_key = first_account.get("binance", {}).get("secret_key")

    binance_client = BinanceClient(api_key, secret_key, proxies=proxies)
    market_data_service = MarketDataService(yfinance_client, binance_client)
    trade_executor = TradeExecutor(binance_client, database, wecom_notifier, system_config)
    strategy_engine = StrategyEngine(market_data_service, binance_client, database, trade_executor)

    logger.info("所有组件初始化完成")

    # 初始化调度器
    scheduler = Scheduler(config_loader, strategy_engine, system_config)
    logger.info("调度器初始化完成")
    print("调度器初始化完成")

    # 准备调用 start
    print("\n准备调用 scheduler.start(accounts)...")
    logger.info("准备调用 scheduler.start(accounts)...")

    # 调用 start
    print("调用 scheduler.start(accounts) 中...")
    logger.info("调用 scheduler.start(accounts) 中...")

    scheduler.start(accounts)

    # 如果执行到这里，说明 start 正常返回了
    print("scheduler.start() 已返回（不应该到达这里）")
    logger.info("scheduler.start() 已返回（不应该到达这里）")

except KeyboardInterrupt:
    print("\n收到 Ctrl+C")
    logger.info("收到键盘中断")
except Exception as e:
    print(f"\n异常: {e}")
    logger.error(f"异常: {e}", exc_info=True)
    import traceback
    traceback.print_exc()
finally:
    if 'database' in locals():
        database.close()
    print("\n程序结束")
    logger.info("程序结束")
