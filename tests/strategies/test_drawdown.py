# tests/strategies/test_drawdown.py
import pytest
import pandas as pd
from strategies.drawdown import DrawdownStrategy

@pytest.fixture
def drawdown_strategy():
    """创建 Drawdown 策略实例"""
    return DrawdownStrategy()

def test_drawdown_get_required_data(drawdown_strategy):
    """测试 Drawdown 数据需求"""
    strategy_config = {"lookback_days": 250}

    requirement = drawdown_strategy.get_required_data(strategy_config)

    assert requirement.history_days == 250
    assert requirement.needs_realtime_price is True

def test_drawdown_calculate_with_drawdown(drawdown_strategy):
    """测试回撤情况下的加仓"""
    strategy_config = {
        "base_amount": 100,
        "lookback_days": 10,
        "sell_rules": []
    }

    # 创建历史数据，最高价 52.10
    history_data = pd.DataFrame({
        'High': [50.0, 52.10, 51.0, 49.0, 48.0]
    })

    market_data = {
        "current_price": 45.32,  # 相对最高价回撤约 13%
        "history_data": history_data,
        "highest_price": 52.10
    }

    signal = drawdown_strategy.calculate({}, strategy_config, market_data, None)

    assert signal.action == "BUY"
    # 基础 100 + 13% 回撤加成 = 113
    assert signal.amount == pytest.approx(113.0, rel=0.01)
    assert "回撤" in signal.reason

def test_drawdown_no_drawdown(drawdown_strategy):
    """测试无回撤情况"""
    strategy_config = {
        "base_amount": 100,
        "lookback_days": 10
    }

    history_data = pd.DataFrame({
        'High': [45.0, 46.0, 47.0]
    })

    market_data = {
        "current_price": 48.0,  # 创新高
        "history_data": history_data,
        "highest_price": 47.0
    }

    signal = drawdown_strategy.calculate({}, strategy_config, market_data, None)

    assert signal.action == "BUY"
    assert signal.amount == 100  # 无回撤，基础金额
