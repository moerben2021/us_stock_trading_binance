# tests/core/test_trade_executor.py
import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from core.trade_executor import TradeExecutor
from strategies.base import TradeSignal

@pytest.fixture
def trade_executor():
    """创建交易执行器"""
    binance_client = Mock()
    database = Mock()
    notifier = Mock()
    system_config = {
        "balance_check": {"insufficient_action": "partial"},
        "retry": {
            "trade_execution": {
                "max_attempts": 3,
                "interval_seconds": 10,
                "backoff": "fixed"
            }
        }
    }

    return TradeExecutor(binance_client, database, notifier, system_config)

def test_execute_buy_trade_success(trade_executor):
    """测试成功执行买入交易"""
    # Mock 余额充足
    trade_executor.binance_client.get_account_balance.return_value = {
        "USDT": {"free": 10000.0, "locked": 0.0}
    }

    # Mock 下单成功
    trade_executor.binance_client.place_order.return_value = {
        "orderId": 12345,
        "executedQty": "2.5",
        "cummulativeQuoteQty": "113.00",
        "status": "FILLED"
    }

    # Mock 实时价格
    trade_executor.binance_client.get_realtime_price.return_value = 45.20

    # Mock 保存交易记录
    trade_executor.database.save_trade.return_value = 1

    # Mock 持仓查询（初始无持仓）
    trade_executor.database.get_position.return_value = None

    signal = TradeSignal(action="BUY", amount=113.0, reason="Test")

    result = trade_executor.execute_trade("alice", "alice_tqqq_dca", signal, "TQQQ", "https://qyapi.weixin.qq.com/webhook")

    assert result["success"] is True
    assert result["trade_id"] == 1
    trade_executor.binance_client.place_order.assert_called_once()
    trade_executor.database.save_trade.assert_called_once()
    trade_executor.notifier.send_trade_notification.assert_called_once()

def test_execute_trade_insufficient_balance_partial(trade_executor):
    """测试余额不足（部分执行）"""
    # Mock 余额不足
    trade_executor.binance_client.get_account_balance.return_value = {
        "USDT": {"free": 50.0, "locked": 0.0}
    }

    trade_executor.binance_client.get_realtime_price.return_value = 45.20
    trade_executor.binance_client.place_order.return_value = {
        "orderId": 12345,
        "executedQty": "1.1",
        "cummulativeQuoteQty": "50.00",
        "status": "FILLED"
    }

    # Mock 持仓查询
    trade_executor.database.get_position.return_value = None
    trade_executor.database.save_trade.return_value = 1

    signal = TradeSignal(action="BUY", amount=113.0, reason="Test")

    result = trade_executor.execute_trade("alice", "alice_tqqq_dca", signal, "TQQQ")

    # 应该按实际余额执行
    assert result["success"] is True
    assert result["adjusted_amount"] == 50.0

def test_execute_trade_insufficient_balance_skip(trade_executor):
    """测试余额不足（跳过）"""
    trade_executor.system_config["balance_check"]["insufficient_action"] = "skip"

    trade_executor.binance_client.get_account_balance.return_value = {
        "USDT": {"free": 50.0, "locked": 0.0}
    }

    signal = TradeSignal(action="BUY", amount=113.0, reason="Test")

    result = trade_executor.execute_trade("alice", "alice_tqqq_dca", signal, "TQQQ")

    # 应该跳过交易
    assert result["success"] is False
    assert "余额不足" in result["error"]
    trade_executor.binance_client.place_order.assert_not_called()

def test_execute_sell_trade(trade_executor):
    """测试卖出交易"""
    trade_executor.binance_client.place_order.return_value = {
        "orderId": 12346,
        "executedQty": "5.0",
        "cummulativeQuoteQty": "226.00",
        "status": "FILLED"
    }

    trade_executor.binance_client.get_realtime_price.return_value = 45.20
    trade_executor.database.save_trade.return_value = 2

    # Mock 持仓查询（有持仓）
    trade_executor.database.get_position.return_value = {
        "quantity": 10.0,
        "avg_cost": 40.0
    }

    signal = TradeSignal(action="SELL", amount=0, quantity=5.0, reason="Test sell")

    result = trade_executor.execute_trade("alice", "alice_tqqq_dca", signal, "TQQQ")

    assert result["success"] is True
    assert result["trade_id"] == 2
