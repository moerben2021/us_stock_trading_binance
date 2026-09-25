"""策略引擎测试"""
import pytest
from unittest.mock import Mock, MagicMock, patch
import pandas as pd
from datetime import datetime
from core.strategy_engine import StrategyEngine
from strategies.base import TradeSignal


@pytest.fixture
def mock_dependencies():
    """创建 Mock 依赖"""
    market_data_service = Mock()
    binance_client = Mock()
    database = Mock()
    trade_executor = Mock()

    return {
        "market_data_service": market_data_service,
        "binance_client": binance_client,
        "database": database,
        "trade_executor": trade_executor
    }


@pytest.fixture
def strategy_engine(mock_dependencies):
    """创建策略引擎实例"""
    return StrategyEngine(
        market_data_service=mock_dependencies["market_data_service"],
        binance_client=mock_dependencies["binance_client"],
        database=mock_dependencies["database"],
        trade_executor=mock_dependencies["trade_executor"]
    )


def test_execute_strategy_success(strategy_engine, mock_dependencies):
    """测试成功执行策略"""
    # 准备账户配置
    account_config = {
        "name": "test_account",
        "api_key": "key123",
        "api_secret": "secret123",
        "webhook_url": "https://webhook.example.com"
    }

    # 准备策略实例配置
    strategy_instance = {
        "id": "strategy_001",
        "type": "dca",
        "symbol": "GOOGL",
        "config": {
            "base_amount": 100.0,
            "sell_rules": []
        }
    }

    # Mock 持仓同步（无差异）
    mock_dependencies["binance_client"].get_position.return_value = {
        "symbol": "GOOGL",
        "quantity": 10.0
    }
    mock_dependencies["database"].get_position.return_value = {
        "account_name": "test_account",
        "symbol": "GOOGL",
        "quantity": 10.0,
        "avg_cost": 150.0
    }

    # Mock 市场数据
    mock_dependencies["market_data_service"].get_market_data.return_value = {
        "history_data": pd.DataFrame(),
        "current_price": 160.0,
        "highest_price": 180.0,
        "lowest_price": 140.0
    }

    # Mock 交易执行
    mock_dependencies["trade_executor"].execute_trade.return_value = {
        "success": True,
        "trade_id": 1001
    }

    # Mock 数据库保存
    mock_dependencies["database"].save_strategy_execution.return_value = 5001

    # 执行策略
    result = strategy_engine.execute_strategy(account_config, strategy_instance)

    # 验证结果
    assert result["success"] is True
    assert result["signal"] == "BUY"
    assert result["execution_id"] == 5001

    # 验证调用了市场数据服务
    mock_dependencies["market_data_service"].get_market_data.assert_called_once()

    # 验证调用了交易执行器
    mock_dependencies["trade_executor"].execute_trade.assert_called_once()

    # 验证保存了执行记录
    mock_dependencies["database"].save_strategy_execution.assert_called_once()


def test_execute_strategy_position_mismatch(strategy_engine, mock_dependencies):
    """测试持仓不匹配时的同步和告警"""
    # 准备账户配置
    account_config = {
        "name": "test_account",
        "api_key": "key123",
        "api_secret": "secret123",
        "webhook_url": "https://webhook.example.com"
    }

    # 准备策略实例配置
    strategy_instance = {
        "id": "strategy_002",
        "type": "dca",
        "symbol": "AAPL",
        "config": {
            "base_amount": 200.0,
            "sell_rules": []
        }
    }

    # Mock 持仓不匹配（Binance 为权威源）
    mock_dependencies["binance_client"].get_position.return_value = {
        "symbol": "AAPL",
        "quantity": 15.0  # Binance 持仓
    }
    mock_dependencies["database"].get_position.return_value = {
        "account_name": "test_account",
        "symbol": "AAPL",
        "quantity": 10.0,  # 本地持仓（不匹配）
        "avg_cost": 150.0
    }

    # Mock WeComNotifier
    with patch('core.strategy_engine.WeComNotifier') as MockNotifier:
        mock_notifier_instance = MockNotifier.return_value
        mock_notifier_instance.send_alert_notification.return_value = True

        # Mock 市场数据
        mock_dependencies["market_data_service"].get_market_data.return_value = {
            "history_data": pd.DataFrame(),
            "current_price": 160.0,
            "highest_price": 180.0,
            "lowest_price": 140.0
        }

        # Mock 交易执行
        mock_dependencies["trade_executor"].execute_trade.return_value = {
            "success": True,
            "trade_id": 1002
        }

        # Mock 数据库保存
        mock_dependencies["database"].save_strategy_execution.return_value = 5002

        # 执行策略
        result = strategy_engine.execute_strategy(account_config, strategy_instance)

        # 验证结果
        assert result["success"] is True

        # 验证更新了本地持仓
        mock_dependencies["database"].update_position.assert_called_once()
        update_call_args = mock_dependencies["database"].update_position.call_args
        assert update_call_args[0][0] == "test_account"
        assert update_call_args[0][1] == "AAPL"
        assert update_call_args[0][2]["quantity"] == 15.0  # 更新为 Binance 的值

        # 验证发送了告警通知
        mock_notifier_instance.send_alert_notification.assert_called_once()


def test_execute_strategy_hold_signal(strategy_engine, mock_dependencies):
    """测试 HOLD 信号不执行交易"""
    account_config = {
        "name": "test_account",
        "api_key": "key123",
        "api_secret": "secret123"
    }

    strategy_instance = {
        "id": "strategy_003",
        "type": "value_averaging",
        "symbol": "MSFT",
        "config": {
            "target_growth_per_period": 100.0,
            "start_date": "2026-09-01",
            "frequency": "monthly"
        }
    }

    # Mock 持仓同步
    mock_dependencies["binance_client"].get_position.return_value = {
        "symbol": "MSFT",
        "quantity": 0.5
    }
    mock_dependencies["database"].get_position.return_value = {
        "account_name": "test_account",
        "symbol": "MSFT",
        "quantity": 0.5,
        "avg_cost": 200.0
    }

    # Mock 市场数据（价格 $200，持仓 0.5 股，市值 $100 = 目标市值）
    mock_dependencies["market_data_service"].get_market_data.return_value = {
        "history_data": pd.DataFrame(),
        "current_price": 200.0,
        "highest_price": 220.0,
        "lowest_price": 180.0
    }

    # Mock 数据库保存
    mock_dependencies["database"].save_strategy_execution.return_value = 5003

    # 执行策略
    result = strategy_engine.execute_strategy(account_config, strategy_instance)

    # 验证结果
    assert result["success"] is True
    assert result["signal"] == "HOLD"

    # 验证没有调用交易执行器
    mock_dependencies["trade_executor"].execute_trade.assert_not_called()

    # 验证保存了执行记录
    mock_dependencies["database"].save_strategy_execution.assert_called_once()


def test_execute_strategy_error_handling(strategy_engine, mock_dependencies):
    """测试错误处理"""
    account_config = {
        "name": "test_account",
        "api_key": "key123",
        "api_secret": "secret123"
    }

    strategy_instance = {
        "id": "strategy_004",
        "type": "dca",
        "symbol": "TSLA",
        "config": {
            "base_amount": 150.0
        }
    }

    # Mock 持仓同步
    mock_dependencies["binance_client"].get_position.return_value = {
        "symbol": "TSLA",
        "quantity": 0.0
    }
    mock_dependencies["database"].get_position.return_value = None

    # Mock 市场数据服务抛出异常
    mock_dependencies["market_data_service"].get_market_data.side_effect = Exception("API 超时")

    # Mock 数据库保存
    mock_dependencies["database"].save_strategy_execution.return_value = 5004

    # 执行策略
    result = strategy_engine.execute_strategy(account_config, strategy_instance)

    # 验证结果
    assert result["success"] is False
    assert "API 超时" in result["error"]

    # 验证保存了失败的执行记录
    mock_dependencies["database"].save_strategy_execution.assert_called_once()
    saved_data = mock_dependencies["database"].save_strategy_execution.call_args[0][0]
    assert saved_data["status"] == "failed"
    assert saved_data["error_message"] is not None
