# tests/strategies/test_value_averaging.py
import pytest
from unittest.mock import patch
from datetime import datetime
from strategies.value_averaging import ValueAveragingStrategy

@pytest.fixture
def va_strategy():
    """创建价值平均策略实例"""
    return ValueAveragingStrategy()

def test_va_get_required_data(va_strategy):
    """测试价值平均数据需求"""
    strategy_config = {"target_growth_per_period": 1000}

    requirement = va_strategy.get_required_data(strategy_config)

    assert requirement.history_days == 30
    assert requirement.needs_realtime_price is True

def test_va_calculate_buy_signal(va_strategy):
    """测试价值平均买入信号"""
    strategy_config = {
        "target_growth_per_period": 1000,
        "start_date": "2026-01-01",
        "frequency": "monthly"
    }

    market_data = {"current_price": 50.0}

    # 当前持仓市值 2000，目标应该是 3000（第3期）
    position = {"quantity": 40.0, "avg_cost": 50.0}

    # Mock 执行次数为 3（第3次执行）
    with patch.object(va_strategy, '_get_execution_count', return_value=3):
        signal = va_strategy.calculate({}, strategy_config, market_data, position)

    # 当前市值 40 * 50 = 2000
    # 目标市值 3 * 1000 = 3000
    # 需要买入 1000
    assert signal.action == "BUY"
    assert signal.amount == pytest.approx(1000, rel=0.01)

def test_va_calculate_sell_signal(va_strategy):
    """测试价值平均卖出信号"""
    strategy_config = {
        "target_growth_per_period": 1000,
        "start_date": "2026-01-01"
    }

    market_data = {"current_price": 50.0}

    # 当前持仓市值 5000，目标应该是 3000
    position = {"quantity": 100.0, "avg_cost": 50.0}

    with patch.object(va_strategy, '_get_execution_count', return_value=3):
        signal = va_strategy.calculate({}, strategy_config, market_data, position)

    # 当前市值 100 * 50 = 5000
    # 目标市值 3 * 1000 = 3000
    # 需要卖出市值 2000，即 40 股
    assert signal.action == "SELL"
    assert signal.quantity == pytest.approx(40.0, rel=0.01)
