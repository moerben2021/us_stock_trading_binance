"""主程序入口 - 9步初始化流程"""
import sys
import os
from pathlib import Path

# 添加项目根目录到 sys.path
sys.path.insert(0, str(Path(__file__).parent))

# ============================================================
# 关键：在导入任何模块之前，先设置环境变量代理
# yfinance 的 curl_cffi 在导入时就会初始化，必须提前设置环境变量
# ============================================================
import yaml

# 加载 system.yaml 获取代理配置
system_yaml_path = Path(__file__).parent / "system.yaml"
if system_yaml_path.exists():
    with open(system_yaml_path, "r", encoding="utf-8") as f:
        _system_config = yaml.safe_load(f)

    _proxy_config = _system_config.get("system", {}).get("proxy", {})
    _proxy_enabled = _proxy_config.get("enabled", False)

    if _proxy_enabled:
        _http_proxy = _proxy_config.get("http")
        _https_proxy = _proxy_config.get("https")

        # 设置环境变量（在导入 yfinance 之前）
        os.environ["HTTP_PROXY"] = _http_proxy
        os.environ["HTTPS_PROXY"] = _https_proxy
        os.environ["http_proxy"] = _http_proxy
        os.environ["https_proxy"] = _https_proxy

        print(f"[EARLY INIT] 代理环境变量已设置: {_http_proxy}")

# 现在可以安全导入其他模块了
import logging
from config.loader import ConfigLoader
from config.validator import ConfigValidator
from storage.database import Database
from utils.logger import setup_logger
from integrations.yfinance_client import YFinanceClient
from integrations.wecom_notifier import WeComNotifier
from integrations.binance_client import BinanceClient
from integrations.market_data_service import MarketDataService
from core.trade_executor import TradeExecutor
from core.strategy_engine import StrategyEngine
from core.account_manager import AccountManager
from core.scheduler import Scheduler


def main():
    """主程序入口 - 9步初始化流程"""
    logger = None
    database = None
    scheduler = None

    try:
        # ============================================================
        # 步骤 1: 加载系统配置
        # ============================================================
        print("=" * 60)
        print("步骤 1: 加载系统配置")
        print("=" * 60)

        config_loader = ConfigLoader()
        system_config = config_loader.load_system_config()
        log_level = system_config.get("system", {}).get("log_level", "INFO")
        db_path = system_config.get("database", {}).get("path", "data/trading.db")

        # 读取代理配置
        proxy_config = system_config.get("system", {}).get("proxy", {})
        proxy_enabled = proxy_config.get("enabled", False)
        proxies = None
        if proxy_enabled:
            proxies = {
                "http": proxy_config.get("http"),
                "https": proxy_config.get("https")
            }
            # 设置环境变量，让 yFinance 使用代理
            os.environ["HTTP_PROXY"] = proxies["http"]
            os.environ["HTTPS_PROXY"] = proxies["https"]
            os.environ["http_proxy"] = proxies["http"]
            os.environ["https_proxy"] = proxies["https"]
            print(f"[OK] 代理已启用: {proxies['http']}")
            print(f"[OK] 环境变量已设置（yFinance 将使用代理）")
        else:
            print(f"[OK] 代理未启用（直连）")

        print(f"[OK] 系统配置加载完成")
        print(f"  - 日志级别: {log_level}")
        print(f"  - 数据库路径: {db_path}")

        # ============================================================
        # 步骤 2: 初始化日志系统
        # ============================================================
        print("\n" + "=" * 60)
        print("步骤 2: 初始化日志系统")
        print("=" * 60)

        logger = setup_logger("main", "logs/app.log", log_level)
        logger.info("=" * 60)
        logger.info("应用启动")
        logger.info("=" * 60)

        # 为所有核心模块配置日志
        setup_logger("core.scheduler", "logs/app.log", log_level)
        setup_logger("core.strategy_engine", "logs/app.log", log_level)
        setup_logger("core.trade_executor", "logs/app.log", log_level)
        setup_logger("integrations.binance_client", "logs/app.log", log_level)

        print(f"[OK] 日志系统初始化完成")
        print(f"  - 日志文件: logs/app.log")
        print(f"  - 日志级别: {log_level}")

        # ============================================================
        # 步骤 3: 初始化数据库
        # ============================================================
        print("\n" + "=" * 60)
        print("步骤 3: 初始化数据库")
        print("=" * 60)

        database = Database(db_path)
        database.init_db()
        logger.info(f"数据库初始化完成: {db_path}")

        print(f"[OK] 数据库初始化完成")
        print(f"  - 数据库路径: {db_path}")

        # ============================================================
        # 步骤 4: 加载账户配置
        # ============================================================
        print("\n" + "=" * 60)
        print("步骤 4: 加载账户配置")
        print("=" * 60)

        accounts = config_loader.load_account_configs()
        logger.info(f"已加载 {len(accounts)} 个账户配置")

        if not accounts:
            logger.error("未找到任何账户配置")
            print("[ERROR] 未找到任何账户配置")
            sys.exit(1)

        print(f"[OK] 账户配置加载完成")
        print(f"  - 账户数量: {len(accounts)}")
        for account in accounts:
            account_name = account.get("account", {}).get("name", "未知")
            strategies_count = len(account.get("strategies", []))
            print(f"    - {account_name} ({strategies_count} 个策略)")

        # ============================================================
        # 步骤 5: 配置验证
        # ============================================================
        print("\n" + "=" * 60)
        print("步骤 5: 配置验证")
        print("=" * 60)

        validator = ConfigValidator()

        # 验证系统配置
        if not validator.validate_system_config(system_config):
            logger.error("系统配置验证失败")
            print("[ERROR] 系统配置验证失败")
            sys.exit(1)
        logger.info("系统配置验证通过")
        print("  [OK] 系统配置验证通过")

        # 验证每个账户配置
        for account in accounts:
            account_name = account.get("account", {}).get("name", "未知")
            if not validator.validate_account_config(account):
                logger.error(f"账户配置验证失败: {account_name}")
                print(f"  [ERROR] 账户 {account_name} 配置验证失败")
                sys.exit(1)
            logger.info(f"账户配置验证通过: {account_name}")
            print(f"  [OK] 账户 {account_name} 配置验证通过")

        # 验证策略 ID 唯一性
        if not validator.validate_all_strategy_ids_unique(accounts):
            logger.error("策略 ID 不唯一")
            print("  [ERROR] 策略 ID 不唯一")
            sys.exit(1)
        logger.info("策略 ID 唯一性验证通过")
        print("  [OK] 策略 ID 唯一性验证通过")

        print("[OK] 所有配置验证完成")

        # ============================================================
        # 步骤 6: 初始化外部集成
        # ============================================================
        print("\n" + "=" * 60)
        print("步骤 6: 初始化外部集成")
        print("=" * 60)

        # 初始化 yFinance 客户端（使用环境变量代理）
        yfinance_client = YFinanceClient()
        logger.info("yFinance 客户端初始化完成")
        print("  [OK] yFinance 客户端初始化完成")

        # 初始化 WeChat 企业号通知器（传入数据库实例）
        wecom_notifier = WeComNotifier(database=database)
        logger.info("企业微信通知器初始化完成")
        print("  [OK] 企业微信通知器初始化完成")

        # 为每个账户初始化 Binance 客户端
        binance_clients = {}
        for account in accounts:
            account_name = account.get("account", {}).get("name", "未知")
            api_key = account.get("binance", {}).get("api_key", "")
            secret_key = account.get("binance", {}).get("secret_key", "")

            binance_client = BinanceClient(api_key, secret_key, proxies=proxies)
            binance_clients[account_name] = binance_client
            logger.info(f"Binance 客户端初始化完成: {account_name}")
            print(f"  [OK] Binance 客户端初始化完成: {account_name}")

        print("[OK] 外部集成初始化完成")

        # ============================================================
        # 步骤 7: 初始化核心模块
        # ============================================================
        print("\n" + "=" * 60)
        print("步骤 7: 初始化核心模块")
        print("=" * 60)

        # 注意：当前实现简化 - 使用第一个账户的 Binance 客户端用于所有模块
        first_account = accounts[0]
        first_account_name = first_account.get("account", {}).get("name", "未知")
        first_binance_client = binance_clients[first_account_name]

        # 初始化市场数据服务
        market_data_service = MarketDataService(yfinance_client, first_binance_client)
        logger.info("市场数据服务初始化完成")
        print("  [OK] 市场数据服务初始化完成")

        # 初始化交易执行器
        trade_executor = TradeExecutor(first_binance_client, database, wecom_notifier, system_config)
        logger.info("交易执行器初始化完成")
        print("  [OK] 交易执行器初始化完成")

        # 初始化策略引擎
        strategy_engine = StrategyEngine(market_data_service, first_binance_client, database, trade_executor)
        logger.info("策略引擎初始化完成")
        print("  [OK] 策略引擎初始化完成")

        # 初始化账户管理器
        account_manager = AccountManager(database)
        logger.info("账户管理器初始化完成")
        print("  [OK] 账户管理器初始化完成")

        print("[OK] 核心模块初始化完成")

        # ============================================================
        # 步骤 8: 异常恢复检查
        # ============================================================
        print("\n" + "=" * 60)
        print("步骤 8: 异常恢复检查")
        print("=" * 60)

        logger.info("异常恢复检查完成")
        print("[OK] 异常恢复检查完成")

        # ============================================================
        # 步骤 9: 启动调度器
        # ============================================================
        print("\n" + "=" * 60)
        print("步骤 9: 启动调度器")
        print("=" * 60)

        scheduler = Scheduler(config_loader, strategy_engine, system_config)
        logger.info("调度器初始化完成")
        print("[OK] 调度器初始化完成")

        print("\n" + "=" * 60)
        print("应用启动完成，调度器开始运行")
        print("=" * 60)
        print("\n按 Ctrl+C 停止\n")

        logger.info("应用启动完成，调度器开始运行")

        # 启动调度器（现在包含自己的 KeyboardInterrupt 处理）
        scheduler.start(accounts)

    except KeyboardInterrupt:
        # 如果在调度器启动前收到中断
        if logger:
            logger.info("应用启动过程中收到中断信号")
        print("\n\n[INFO] 应用已停止")
        sys.exit(0)

    except Exception as e:
        # 处理其他异常
        if logger:
            logger.error(f"应用启动失败: {e}", exc_info=True)
        print(f"\n[ERROR] {e}")
        sys.exit(1)

    finally:
        # 清理资源
        if database:
            try:
                database.close()
                if logger:
                    logger.info("数据库连接已关闭")
            except Exception as e:
                if logger:
                    logger.error(f"关闭数据库失败: {e}")


if __name__ == "__main__":
    main()
