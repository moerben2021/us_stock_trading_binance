"""调度器 - APScheduler 任务调度"""
import logging
import signal
import sys
import re
import time
from datetime import datetime
from typing import Dict, Any, List
from apscheduler.schedulers.background import BackgroundScheduler
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

        # 创建后台调度器（非阻塞）
        self.scheduler = BackgroundScheduler()

        logger.info("调度器初始化完成")

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

            # 启动后台调度器（非阻塞）
            logger.info("调度器开始运行...")
            self.scheduler.start()

            # 主线程保持运行，等待 KeyboardInterrupt
            print("\n[INFO] 调度器运行中，已注册任务:")
            for job in self.scheduler.get_jobs():
                print(f"  - {job.id}: 下次运行 {job.next_run_time}")
            print()

            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("收到键盘中断信号，准备关闭调度器...")
                print("\n[INFO] 正在停止调度器，请稍候...")
                self.scheduler.shutdown(wait=False)
                logger.info("调度器已关闭")
                print("[INFO] 调度器已停止")

        except Exception as e:
            logger.error(f"调度器启动失败: {e}", exc_info=True)
            raise

    def _validate_cron_field(self, field: str, min_val: int, max_val: int, field_name: str) -> bool:
        """
        验证 cron 字段的安全性

        Args:
            field: cron 字段值
            min_val: 最小值
            max_val: 最大值
            field_name: 字段名称（用于日志）

        Returns:
            是否合法
        """
        if field == '*':
            return True

        # 只允许数字、*、-、/、, 这些合法的 cron 字符
        if not re.match(r'^[0-9*,/-]+$', field):
            logger.error(f"Cron 字段 {field_name} 包含非法字符: {field}")
            return False

        # 验证数字范围（如果是纯数字）
        if field.isdigit():
            val = int(field)
            if not (min_val <= val <= max_val):
                logger.error(f"Cron 字段 {field_name} 超出范围 [{min_val}-{max_val}]: {val}")
                return False

        # 验证范围表达式 (如 1-5)
        if '-' in field and '/' not in field:
            try:
                start, end = field.split('-')
                if not (min_val <= int(start) <= max_val and min_val <= int(end) <= max_val):
                    logger.error(f"Cron 范围 {field_name} 超出界限: {field}")
                    return False
            except (ValueError, AttributeError):
                logger.error(f"Cron 范围 {field_name} 格式错误: {field}")
                return False

        # 验证步长表达式 (如 */5 或 1-10/2)
        if '/' in field:
            try:
                base, step = field.split('/')
                step_val = int(step)
                if step_val <= 0 or step_val > max_val:
                    logger.error(f"Cron 步长 {field_name} 无效: {step_val}")
                    return False
            except (ValueError, AttributeError):
                logger.error(f"Cron 步长 {field_name} 格式错误: {field}")
                return False

        return True

    def _schedule_strategy(self, account: Dict[str, Any], strategy: Dict[str, Any]):
        """
        为策略创建调度任务

        Args:
            account: 账户配置
            strategy: 策略配置
        """
        strategy_id = strategy.get("id")
        schedule = strategy.get("schedule")  # 使用 cron 表达式

        if not schedule:
            logger.warning(f"策略 {strategy_id} 缺少 schedule 配置，跳过调度")
            return

        logger.info(f"调度策略: {strategy_id}, schedule={schedule}")

        try:
            # 第一步：验证 cron 表达式整体格式
            # 格式: "分 时 日 月 星期"
            cron_pattern = r'^[0-9*,-/]+ +[0-9*,-/]+ +[0-9*,-/]+ +[0-9*,-/]+ +([0-9*,-/]+|MON|TUE|WED|THU|FRI|SAT|SUN)$'
            if not re.match(cron_pattern, schedule, re.IGNORECASE):
                logger.error(f"策略 {strategy_id} 的 cron 表达式格式错误: {schedule}")
                return

            # 解析 cron 表达式
            parts = schedule.split()

            if len(parts) != 5:
                logger.error(f"策略 {strategy_id} 的 cron 表达式字段数量错误: {schedule}")
                return

            minute, hour, day, month, day_of_week = parts

            # 第二步：验证每个字段的安全性和范围
            if not self._validate_cron_field(minute, 0, 59, "minute"):
                logger.error(f"策略 {strategy_id} 的 minute 字段验证失败")
                return
            if not self._validate_cron_field(hour, 0, 23, "hour"):
                logger.error(f"策略 {strategy_id} 的 hour 字段验证失败")
                return
            if not self._validate_cron_field(day, 1, 31, "day"):
                logger.error(f"策略 {strategy_id} 的 day 字段验证失败")
                return
            if not self._validate_cron_field(month, 1, 12, "month"):
                logger.error(f"策略 {strategy_id} 的 month 字段验证失败")
                return

            # 构建 CronTrigger 参数
            trigger_kwargs = {"timezone": "America/New_York"}

            if minute != "*":
                trigger_kwargs["minute"] = minute
            if hour != "*":
                trigger_kwargs["hour"] = hour
            if day != "*":
                trigger_kwargs["day"] = day
            if month != "*":
                trigger_kwargs["month"] = month
            if day_of_week != "*":
                # 转换星期缩写到数字 (MON=0, TUE=1, ..., SUN=6)
                day_map = {
                    "MON": 0, "TUE": 1, "WED": 2, "THU": 3,
                    "FRI": 4, "SAT": 5, "SUN": 6
                }
                if day_of_week.upper() in day_map:
                    trigger_kwargs["day_of_week"] = day_map[day_of_week.upper()]
                else:
                    # 如果是数字形式的星期，验证范围
                    if not self._validate_cron_field(day_of_week, 0, 6, "day_of_week"):
                        logger.error(f"策略 {strategy_id} 的 day_of_week 字段验证失败")
                        return
                    trigger_kwargs["day_of_week"] = day_of_week

            trigger = CronTrigger(**trigger_kwargs)

            # 添加任务到调度器
            job_id = f"{account.get('account', {}).get('name')}:{strategy_id}"
            job = self.scheduler.add_job(
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
