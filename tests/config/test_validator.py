import pytest
from config.validator import ConfigValidator


def test_validate_system_config_valid():
    """测试验证有效的系统配置"""
    config = {
        "system": {"timezone": "America/New_York", "log_level": "INFO"},
        "scheduler": {"check_interval": 60, "manual_trade_scan_interval": 30},
        "database": {"path": "data/trading.db"},
        "retry": {
            "api_call": {"max_attempts": 3, "interval_seconds": 5, "backoff": "exponential"}
        },
        "notifications": {"admin_webhook": "https://example.com"},
        "balance_check": {"insufficient_action": "partial"}
    }

    assert ConfigValidator.validate_system_config(config) is True


def test_validate_system_config_missing_key():
    """测试缺少必需字段的系统配置"""
    config = {
        "system": {"timezone": "America/New_York", "log_level": "INFO"}
    }

    assert ConfigValidator.validate_system_config(config) is False


def test_validate_system_config_invalid_log_level():
    """测试无效的日志级别"""
    config = {
        "system": {"timezone": "America/New_York", "log_level": "INVALID"},
        "scheduler": {"check_interval": 60, "manual_trade_scan_interval": 30},
        "database": {"path": "data/trading.db"},
        "retry": {},
        "notifications": {}
    }

    assert ConfigValidator.validate_system_config(config) is False


def test_validate_account_config_valid():
    """测试验证有效的账户配置"""
    config = {
        "account": {"name": "alice", "wecom_webhook": "https://example.com"},
        "strategies": [
            {
                "id": "alice_tqqq_dca",
                "type": "DCA",
                "symbol": "TQQQ",
                "config": {"base_amount": 100},
                "status": "active"
            }
        ],
        "binance": {"api_key": "test_key", "secret_key": "test_secret"}
    }

    assert ConfigValidator.validate_account_config(config) is True


def test_validate_account_config_missing_account():
    """测试缺少账户信息"""
    config = {
        "strategies": [],
        "binance": {"api_key": "test_key", "secret_key": "test_secret"}
    }

    assert ConfigValidator.validate_account_config(config) is False


def test_validate_account_config_duplicate_strategy_id():
    """测试重复的策略 ID"""
    config = {
        "account": {"name": "alice"},
        "strategies": [
            {"id": "strategy1", "type": "DCA", "symbol": "TQQQ", "config": {"base_amount": 100}, "status": "active"},
            {"id": "strategy1", "type": "DCA", "symbol": "SOXL", "config": {"base_amount": 100}, "status": "active"}
        ],
        "binance": {"api_key": "test_key", "secret_key": "test_secret"}
    }

    assert ConfigValidator.validate_account_config(config) is False


def test_validate_strategy_config_dca():
    """测试 DCA 策略验证"""
    strategy = {
        "id": "test_dca",
        "type": "DCA",
        "symbol": "TQQQ",
        "config": {"base_amount": 100},
        "status": "active"
    }

    assert ConfigValidator.validate_strategy_config(strategy) is True


def test_validate_strategy_config_invalid_type():
    """测试无效的策略类型"""
    strategy = {
        "id": "test_invalid",
        "type": "INVALID",
        "symbol": "TQQQ",
        "config": {},
        "status": "active"
    }

    assert ConfigValidator.validate_strategy_config(strategy) is False


def test_validate_strategy_config_value_averaging_with_sell_rules():
    """测试价值平均策略不应该有 sell_rules"""
    strategy = {
        "id": "test_va",
        "type": "ValueAveraging",
        "symbol": "TQQQ",
        "config": {
            "target_growth_per_period": 100,
            "sell_rules": {"trigger": "profit"}
        },
        "status": "active"
    }

    assert ConfigValidator.validate_strategy_config(strategy) is False


def test_validate_all_strategy_ids_unique():
    """测试全局策略 ID 唯一性"""
    accounts = [
        {
            "account": {"name": "alice"},
            "strategies": [
                {"id": "strategy1", "type": "DCA"},
                {"id": "strategy2", "type": "DCA"}
            ]
        },
        {
            "account": {"name": "bob"},
            "strategies": [
                {"id": "strategy3", "type": "DCA"}
            ]
        }
    ]

    assert ConfigValidator.validate_all_strategy_ids_unique(accounts) is True


def test_validate_all_strategy_ids_not_unique():
    """测试全局策略 ID 不唯一"""
    accounts = [
        {
            "account": {"name": "alice"},
            "strategies": [
                {"id": "strategy1", "type": "DCA"}
            ]
        },
        {
            "account": {"name": "bob"},
            "strategies": [
                {"id": "strategy1", "type": "DCA"}
            ]
        }
    ]

    assert ConfigValidator.validate_all_strategy_ids_unique(accounts) is False
