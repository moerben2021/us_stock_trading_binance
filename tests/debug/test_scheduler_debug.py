"""诊断调度器启动问题"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

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
import yaml

print("=" * 60)
print("调度器启动诊断")
print("=" * 60)
print()

# 初始化日志
logger = setup_logger("test", "logs/test_scheduler_debug.log", "DEBUG")
logger.info("诊断开始")

# 加载配置
config_loader = ConfigLoader()
system_config = config_loader.load_system_config()
accounts = config_loader.load_account_configs()

print(f"加载了 {len(accounts)} 个账户")
print(f"第一个账户: {accounts[0].get('account', {}).get('name')}")
print(f"策略数量: {len(accounts[0].get('strategies', []))}")
print()

# 初始化必要组件
proxy_config = system_config.get("system", {}).get("proxy", {})
proxies = None
if proxy_config.get("enabled", False):
    proxies = {
        "http": proxy_config.get("http"),
        "https": proxy_config.get("https")
    }

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

print("所有组件初始化完成")
print()

# 初始化调度器
print("初始化调度器...")
scheduler = Scheduler(config_loader, strategy_engine, system_config)
print("调度器初始化完成")
print()

# 尝试启动调度器
print("准备调用 scheduler.start()...")
print()

try:
    # 不实际启动 while 循环，只测试调度器配置
    logger.info("测试启动调度器...")

    # 手动执行 start 方法的前半部分
    for account in accounts:
        account_name = account.get("account", {}).get("name")
        strategies = account.get("strategies", [])

        print(f"处理账户: {account_name}")
        logger.info(f"处理账户: {account_name}, 策略数量: {len(strategies)}")

        for strategy in strategies:
            strategy_id = strategy.get("id")
            status = strategy.get("status")
            schedule = strategy.get("schedule")

            print(f"  策略: {strategy_id}")
            print(f"    状态: {status}")
            print(f"    调度: {schedule}")

            if status == "active":
                print(f"    -> 将调度此策略")
                # 尝试调度
                scheduler._schedule_strategy(account, strategy)
            else:
                print(f"    -> 跳过（非活跃）")

    print()
    print("启动调度器...")
    scheduler.scheduler.start()

    print("已注册的任务:")
    jobs = scheduler.scheduler.get_jobs()
    print(f"任务数量: {len(jobs)}")

    for job in jobs:
        print(f"  - {job.id}")
        print(f"    下次运行: {job.next_run_time}")
        print(f"    触发器: {job.trigger}")

    print()
    print("[SUCCESS] 调度器配置成功!")
    print()
    print("如果要实际运行，程序会在这里进入 while True 循环等待任务执行")

    # 关闭调度器
    scheduler.scheduler.shutdown(wait=False)

except Exception as e:
    print(f"[ERROR] 调度器启动失败: {e}")
    import traceback
    traceback.print_exc()
    logger.error(f"调度器启动失败: {e}", exc_info=True)

finally:
    database.close()
    print()
    print("=" * 60)
    print("诊断完成")
    print("=" * 60)
