# strategies/dca.py
"""DCA (固定金额定投) 策略"""
import logging
from typing import Dict, Any, Optional
from strategies.base import BaseStrategy, TradeSignal, DataRequirement

logger = logging.getLogger(__name__)

class DCAStrategy(BaseStrategy):
    """
    DCA (Dollar-Cost Averaging) 策略
    固定金额定投，不考虑市场波动
    """

    def calculate(
        self,
        account_config: Dict[str, Any],
        strategy_config: Dict[str, Any],
        market_data: Dict[str, Any],
        position: Optional[Dict[str, Any]]
    ) -> TradeSignal:
        """
        计算交易信号

        DCA 策略逻辑：
        1. 先检查卖出规则
        2. 如果没有触发卖出，返回固定金额的买入信号
        """
        current_price = market_data.get("current_price", 0)

        # 检查卖出规则
        sell_signal = self.check_sell_rules(strategy_config, position, current_price)
        if sell_signal:
            logger.info(f"DCA 策略触发卖出规则: {sell_signal.reason}")
            return sell_signal

        # 返回固定金额买入信号
        base_amount = strategy_config.get("base_amount", 0)

        logger.info(f"DCA 策略：固定买入 ${base_amount}")

        return TradeSignal(
            action="BUY",
            amount=base_amount,
            reason=f"DCA 固定金额定投"
        )

    def get_required_data(self, strategy_config: Dict[str, Any]) -> DataRequirement:
        """
        DCA 策略只需要实时价格
        """
        return DataRequirement(
            history_days=0,
            needs_realtime_price=True
        )
