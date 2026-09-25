"""调度器 - APScheduler 任务调度"""
import logging
import signal
import sys
from datetime import datetime
from typing import Dict, Any, List
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)


class Scheduler:
    """任务调度器 - 使用 APScheduler 协调策略执行"""

    def __init__(self, config_loader, strategy_engine, system_config: Dict[str, Any]):
        """
        初始化调度器

        Args:
            config_loader: 配置加载器
            strategy_engine: 策略引擎
            system_config: 系统配置
        """
        self.config_loader = config_loader
        self.strategy_engine = strategy_engine
        self.system_config = system_config

        # 创建阻塞式调度器
        self.scheduler = BlockingScheduler()

        # 注册信号处理器以实现优雅退出
        self._register_signal_handlers()

        logger.info("调度器初始化完成")

    def _register_signal_handlers(self):
        """注册信号处理器以实现优雅退出"""
        def signal_handler(signum, frame):
            logger.info(f"收到信号 {signum}，准备优雅关闭调度器...")
            self.scheduler.shutdown(wait=True)
            logger.info("调度器已关闭")
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def start(self, accounts: List[Dict[str, Any]]):
        """
        启动调度器

        Args:
            accounts: 账户列表
        """
        logger.info("启动调度器...")

        try:
            # 遍历账户及其策略
            for account in accounts:
                account_name = account.get("account", {}).get("name")
                strategies = account.get("strategies", [])

                logger.info(f"处理账户: {account_name}, 策略数量: {len(strategies)}")

                for strategy in strategies:
                    # 只调度状态为 "active" 的策略
                    if strategy.get("status") == "active":
                        self._schedule_strategy(account, strategy)
                    else:
                        logger.debug(
                            f"跳过非活跃策略: {strategy.get('id')} "
                            f"(status={strategy.get('status')})"
                        )

            # 添加手动交易扫描任务
            self._add_manual_trade_scanner_job()

            # 启动调度器（阻塞式）
            logger.info("调度器开始运行...")
            self.scheduler.start()

        except Exception as e:
            logger.error(f"调度器启动失败: {e}", exc_info=True)
            raise

    def _schedule_strategy(self, account: Dict[str, Any], strategy: Dict[str, Any]):
        """
        为策略创建调度任务

        Args:
            account: 账户配置
            strategy: 策略配置
        """
        strategy_id = strategy.get("id")
        frequency = strategy.get("frequency", "monthly")

        logger.info(f"调度策略: {strategy_id}, frequency={frequency}")

        try:
            # 根据频率创建触发器
            if frequency == "daily":
                trigger = CronTrigger(
                    hour=9,
                    minute=0,
                    timezone="America/New_York"
                )
            elif frequency == "weekly":
                trigger = CronTrigger(
                    day_of_week=0,  # Monday
                    hour=9,
                    minute=0,
                    timezone="America/New_York"
                )
            elif frequency == "monthly":
                trigger = CronTrigger(
                    day=1,
                    hour=9,
                    minute=0,
                    timezone="America/New_York"
                )
            else:
                logger.warning(f"未知的策略频率: {frequency}, 使用月度频率")
                trigger = CronTrigger(
                    day=1,
                    hour=9,
                    minute=0,
                    timezone="America/New_York"
                )

            # 添加任务到调度器
            job_id = f"{account.get('account', {}).get('name')}:{strategy_id}"
            self.scheduler.add_job(
                self._execute_strategy_job,
                trigger=trigger,
                args=[account, strategy],
                id=job_id,
                name=f"Strategy: {strategy_id}",
                replace_existing=True
            )

            logger.info(f"策略已调度: {job_id}")

        except Exception as e:
            logger.error(f"调度策略失败: {strategy_id}, {e}", exc_info=True)

    def _execute_strategy_job(self, account: Dict[str, Any], strategy: Dict[str, Any]):
        """
        策略执行任务（由调度器调用）

        Args:
            account: 账户配置
            strategy: 策略配置
        """
        strategy_id = strategy.get("id")
        account_name = account.get("account", {}).get("name")

        logger.info(f"执行策略任务: {strategy_id} for {account_name}")

        try:
            result = self.strategy_engine.execute_strategy(account, strategy)

            if result.get("success"):
                logger.info(
                    f"策略执行成功: {strategy_id}, "
                    f"signal={result.get('signal')}, "
                    f"execution_id={result.get('execution_id')}"
                )
            else:
                logger.warning(
                    f"策略执行失败: {strategy_id}, "
                    f"error={result.get('error')}"
                )
        except Exception as e:
            logger.error(f"策略执行异常: {strategy_id}, {e}", exc_info=True)

    def _add_manual_trade_scanner_job(self):
        """添加手动交易扫描任务"""
        interval = self.system_config.get("scheduler", {}).get("manual_trade_scan_interval", 60)

        logger.info(f"添加手动交易扫描任务 (interval={interval}s)")

        try:
            trigger = IntervalTrigger(seconds=interval)

            self.scheduler.add_job(
                self._scan_manual_trades,
                trigger=trigger,
                id="manual_trade_scanner",
                name="Manual Trade Scanner",
                replace_existing=True
            )

            logger.info("手动交易扫描任务已添加")

        except Exception as e:
            logger.error(f"添加手动交易扫描任务失败: {e}", exc_info=True)

    def _scan_manual_trades(self):
        """
        扫描手动交易配置

        NOTE: 手动交易执行是 TODO（该任务仅简化实现）
        """
        try:
            manual_trades = self.config_loader.load_manual_trade_configs()

            if manual_trades:
                logger.info(f"发现手动交易配置: {len(manual_trades)} 个")
                # TODO: 实现手动交易执行逻辑
            else:
                logger.debug("没有待处理的手动交易")
        except Exception as e:
            logger.error(f"扫描手动交易失败: {e}", exc_info=True)
