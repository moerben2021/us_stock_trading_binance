# tests/strategies/test_base.py
import pytest
from strategies.base import BaseStrategy, TradeSignal, DataRequirement

def test_trade_signal_creation():
    """测试交易信号创建"""
    signal = TradeSignal(
        action="BUY",
        amount=100.0,
        reason="DCA 定投"
    )

    assert signal.action == "BUY"
    assert signal.amount == 100.0
    assert signal.reason == "DCA 定投"

def test_data_requirement_creation():
    """测试数据需求创建"""
    requirement = DataRequirement(
        history_days=250,
        needs_realtime_price=True
    )

    assert requirement.history_days == 250
    assert requirement.needs_realtime_price is True

def test_base_strategy_is_abstract():
    """测试基类是抽象的"""
    with pytest.raises(TypeError):
        # 不能直接实例化抽象类
        BaseStrategy()
