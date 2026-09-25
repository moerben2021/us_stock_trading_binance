# strategies/drawdown.py
"""Drawdown (回撤加仓) 策略"""
import logging
from typing import Dict, Any, Optional
from strategies.base import BaseStrategy, TradeSignal, DataRequirement

logger = logging.getLogger(__name__)

class DrawdownStrategy(BaseStrategy):
    """
    Drawdown 回撤加仓策略
    根据当前价格相对历史最高价的回撤幅度，动态调整定投金额
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

        Drawdown 策略逻辑：
        1. 先检查卖出规则
        2. 计算回撤幅度
        3. 根据回撤幅度调整买入金额：基础金额 × (1 + 回撤百分比)
        """
        current_price = market_data.get("current_price", 0)

        # 检查卖出规则
        sell_signal = self.check_sell_rules(strategy_config, position, current_price)
        if sell_signal:
            logger.info(f"Drawdown 策略触发卖出规则: {sell_signal.reason}")
            return sell_signal

        # 获取历史最高价
        history_data = market_data.get("history_data")
        if history_data is not None and not history_data.empty:
            highest_price = history_data['High'].max()
        else:
            highest_price = market_data.get("highest_price", current_price)

        # 计算回撤幅度
        if highest_price > 0:
            drawdown_pct = (highest_price - current_price) / highest_price * 100
            drawdown_pct = max(0, drawdown_pct)  # 回撤不能为负
        else:
            drawdown_pct = 0

        # 计算投入金额
        base_amount = strategy_config.get("base_amount", 0)
        adjusted_amount = base_amount * (1 + drawdown_pct / 100)

        logger.info(
            f"Drawdown 策略：最高价 ${highest_price:.2f}, "
            f"当前价 ${current_price:.2f}, 回撤 {drawdown_pct:.2f}%, "
            f"投入金额 ${adjusted_amount:.2f}"
        )

        return TradeSignal(
            action="BUY",
            amount=adjusted_amount,
            reason=f"Drawdown 回撤加仓（回撤 {drawdown_pct:.2f}%）"
        )

    def get_required_data(self, strategy_config: Dict[str, Any]) -> DataRequirement:
        """
        Drawdown 策略需要历史数据和实时价格
        """
        lookback_days = strategy_config.get("lookback_days", 250)

        return DataRequirement(
            history_days=lookback_days,
            needs_realtime_price=True
        )
