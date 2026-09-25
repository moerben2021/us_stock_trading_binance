"""配置验证器"""
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class ConfigValidator:
    """配置验证器"""

    @staticmethod
    def validate_system_config(config: Dict[str, Any]) -> bool:
        """
        验证系统配置

        Args:
            config: 系统配置

        Returns:
            是否合法
        """
        required_keys = ["system", "scheduler", "database", "retry", "notifications"]

        for key in required_keys:
            if key not in config:
                logger.error(f"系统配置缺少必需字段: {key}")
                return False

        # 验证日志级别
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        log_level = config["system"].get("log_level", "INFO")
        if log_level not in valid_log_levels:
            logger.error(f"无效的日志级别: {log_level}")
            return False

        # 验证余额不足处理策略
        insufficient_action = config.get("balance_check", {}).get("insufficient_action", "partial")
        if insufficient_action not in ["partial", "skip"]:
            logger.error(f"无效的余额不足处理策略: {insufficient_action}")
            return False

        return True

    @staticmethod
    def validate_account_config(config: Dict[str, Any]) -> bool:
        """
        验证账户配置

        Args:
            config: 账户配置

        Returns:
            是否合法
        """
        # 验证账户基本信息
        if "account" not in config:
            logger.error("账户配置缺少 account 字段")
            return False

        if "name" not in config["account"]:
            logger.error("账户配置缺少 name 字段")
            return False

        # 验证策略列表
        if "strategies" not in config or not isinstance(config["strategies"], list):
            logger.error("账户配置缺少 strategies 字段或类型错误")
            return False

        # 验证每个策略
        strategy_ids = set()
        for strategy in config["strategies"]:
            if not ConfigValidator.validate_strategy_config(strategy):
                return False

            # 检查策略 ID 唯一性
            strategy_id = strategy.get("id")
            if strategy_id in strategy_ids:
                logger.error(f"策略 ID 重复: {strategy_id}")
                return False
            strategy_ids.add(strategy_id)

        # 验证 Binance API 密钥
        if "binance" not in config:
            logger.error("账户配置缺少 binance 密钥信息")
            return False

        if "api_key" not in config["binance"] or "secret_key" not in config["binance"]:
            logger.error("账户配置缺少 api_key 或 secret_key")
            return False

        return True

    @staticmethod
    def validate_strategy_config(strategy: Dict[str, Any]) -> bool:
        """
        验证策略配置

        Args:
            strategy: 策略配置

        Returns:
            是否合法
        """
        required_keys = ["id", "type", "symbol", "config", "status"]

        for key in required_keys:
            if key not in strategy:
                logger.error(f"策略配置缺少必需字段: {key}")
                return False

        # 验证策略类型
        valid_types = ["DCA", "Drawdown", "ValueAveraging"]
        if strategy["type"] not in valid_types:
            logger.error(f"无效的策略类型: {strategy['type']}")
            return False

        # 验证策略状态
        valid_statuses = ["active", "paused"]
        if strategy["status"] not in valid_statuses:
            logger.error(f"无效的策略状态: {strategy['status']}")
            return False

        # 验证策略配置
        config = strategy["config"]
        strategy_type = strategy["type"]

        if strategy_type == "DCA":
            if "base_amount" not in config:
                logger.error("DCA 策略缺少 base_amount 配置")
                return False
        elif strategy_type == "Drawdown":
            if "base_amount" not in config or "lookback_days" not in config:
                logger.error("Drawdown 策略缺少 base_amount 或 lookback_days 配置")
                return False
        elif strategy_type == "ValueAveraging":
            if "target_growth_per_period" not in config:
                logger.error("ValueAveraging 策略缺少 target_growth_per_period 配置")
                return False
            # 价值平均策略不应该有 sell_rules
            if "sell_rules" in config:
                logger.error("ValueAveraging 策略不支持额外的 sell_rules")
                return False

        return True

    @staticmethod
    def validate_all_strategy_ids_unique(accounts: List[Dict[str, Any]]) -> bool:
        """
        验证所有账户的策略 ID 全局唯一

        Args:
            accounts: 账户配置列表

        Returns:
            是否唯一
        """
        all_strategy_ids = set()

        for account in accounts:
            for strategy in account.get("strategies", []):
                strategy_id = strategy.get("id")
                if strategy_id in all_strategy_ids:
                    logger.error(f"策略 ID 在多个账户中重复: {strategy_id}")
                    return False
                all_strategy_ids.add(strategy_id)

        return True
