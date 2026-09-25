# tests/strategies/test_dca.py
import pytest
from strategies.dca import DCAStrategy
from strategies.base import TradeSignal

@pytest.fixture
def dca_strategy():
    """创建 DCA 策略实例"""
    return DCAStrategy()

def test_dca_get_required_data(dca_strategy):
    """测试 DCA 数据需求"""
    strategy_config = {"base_amount": 100}

    requirement = dca_strategy.get_required_data(strategy_config)

    assert requirement.history_days == 0
    assert requirement.needs_realtime_price is True

def test_dca_calculate_buy_signal(dca_strategy):
    """测试 DCA 买入信号"""
    account_config = {"name": "alice"}
    strategy_config = {
        "base_amount": 100,
        "sell_rules": []
    }
    market_data = {"current_price": 45.20}
    position = None

    signal = dca_strategy.calculate(account_config, strategy_config, market_data, position)

    assert signal.action == "BUY"
    assert signal.amount == 100
    assert "DCA" in signal.reason

def test_dca_with_sell_rule_triggered(dca_strategy):
    """测试 DCA 卖出规则触发"""
    strategy_config = {
        "base_amount": 100,
        "sell_rules": [
            {
                "type": "profit_percentage",
                "threshold": 30,
                "sell_type": "position_percentage",
                "sell_amount": 50
            }
        ]
    }
    market_data = {"current_price": 65.0}
    position = {"quantity": 10.0, "avg_cost": 50.0}

    signal = dca_strategy.calculate({}, strategy_config, market_data, position)

    # 盈利 30%，应该触发卖出
    assert signal.action == "SELL"
    assert signal.quantity == 5.0  # 50% 的持仓
