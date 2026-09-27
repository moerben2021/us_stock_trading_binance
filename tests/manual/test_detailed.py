"""最详细的调度器调用测试"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

print("[STEP 0] 开始导入...")

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

print("[STEP 1] 导入完成，开始初始化日志...")

logger = setup_logger("main", "logs/test_detailed.log", "DEBUG")
logger.info("测试开始")

print("[STEP 2] 开始加载配置...")

try:
    config_loader = ConfigLoader()
    system_config = config_loader.load_system_config()
    accounts = config_loader.load_account_configs()

    print(f"[STEP 3] 配置加载完成，账户数: {len(accounts)}")

    # 初始化所有组件
    proxy_config = system_config.get("system", {}).get("proxy", {})
    proxies = None
    if proxy_config.get("enabled", False):
        proxies = {"http": proxy_config.get("http"), "https": proxy_config.get("https")}

    database = Database("data/trading.db")
    database.init_db()

    yfinance_client = YFinanceClient()
    wecom_notifier = WeComNotifier()

    first_account = accounts[0]
    api_key = first_account.get("binance", {}).get("api_key")
    secret_key = first_account.get("binance", {}).get("secret_key")

    binance_client = BinanceClient(api_key, secret_key, proxies=proxies)
    market_data_service = MarketDataService(yfinance_client, binance_client)
    trade_executor = TradeExecutor(binance_client, database, wecom_notifier, system_config)
    strategy_engine = StrategyEngine(market_data_service, binance_client, database, trade_executor)

    print("[STEP 4] 所有组件初始化完成")

    # 初始化调度器
    print("[STEP 5] 开始初始化调度器...")
    scheduler = Scheduler(config_loader, strategy_engine, system_config)
    print("[STEP 6] 调度器初始化完成")

    # 准备调用 start
    print("[STEP 7] 准备调用 scheduler.start(accounts)...")
    print(f"[STEP 7.1] accounts 类型: {type(accounts)}")
    print(f"[STEP 7.2] accounts 长度: {len(accounts)}")
    print(f"[STEP 7.3] scheduler 对象: {scheduler}")
    print(f"[STEP 7.4] scheduler.start 方法: {scheduler.start}")

    print("[STEP 8] 即将调用 scheduler.start(accounts)...")
    sys.stdout.flush()  # 强制刷新输出

    # 调用 start
    print("[STEP 9] 正在调用 scheduler.start(accounts)...")
    sys.stdout.flush()

    scheduler.start(accounts)

    # 如果到达这里，说明 start 返回了
    print("[STEP 10] scheduler.start() 已返回（不应该到达这里）")

except KeyboardInterrupt:
    print("\n[EXIT] 收到 Ctrl+C")
    logger.info("收到键盘中断")
except Exception as e:
    print(f"\n[ERROR] 捕获异常: {e}")
    logger.error(f"异常: {e}", exc_info=True)
    import traceback
    traceback.print_exc()
    sys.stdout.flush()
finally:
    if 'database' in locals():
        database.close()
    print("\n[END] 测试结束")
    logger.info("测试结束")
    sys.stdout.flush()
