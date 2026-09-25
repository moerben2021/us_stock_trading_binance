# strategies/value_averaging.py
"""ValueAveraging (价值平均) 策略"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from strategies.base import BaseStrategy, TradeSignal, DataRequirement

logger = logging.getLogger(__name__)

class ValueAveragingStrategy(BaseStrategy):
    """
    价值平均策略（纯粹版）
    设定目标价值增长路径，根据当前市值与目标的差额进行买入或卖出
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

        价值平均策略逻辑：
        1. 计算目标持仓市值
        2. 计算当前持仓市值
        3. 根据差额决定买入或卖出
        """
        current_price = market_data.get("current_price", 0)
        target_growth = strategy_config.get("target_growth_per_period", 0)

        # 计算执行次数（从起始日期到现在）
        execution_count = self._get_execution_count(strategy_config)

        # 目标市值 = 执行次数 × 每期目标增长
        target_value = execution_count * target_growth

        # 当前持仓市值
        if position and position.get("quantity", 0) > 0:
            current_value = position["quantity"] * current_price
        else:
            current_value = 0

        # 计算差额
        difference = target_value - current_value

        logger.info(
            f"价值平均策略：执行次数 {execution_count}, "
            f"目标市值 ${target_value:.2f}, 当前市值 ${current_value:.2f}, "
            f"差额 ${difference:.2f}"
        )

        if difference > 0:
            # 需要买入
            return TradeSignal(
                action="BUY",
                amount=difference,
                reason=f"价值平均买入（补足差额 ${difference:.2f}）"
            )
        elif difference < 0:
            # 需要卖出
            sell_value = abs(difference)
            sell_quantity = sell_value / current_price if current_price > 0 else 0

            return TradeSignal(
                action="SELL",
                amount=sell_value,
                quantity=sell_quantity,
                reason=f"价值平均卖出（超出目标 ${sell_value:.2f}）"
            )
        else:
            # 刚好达到目标，不操作
            return TradeSignal(
                action="HOLD",
                amount=0,
                reason="价值平均：当前市值等于目标市值"
            )

    def get_required_data(self, strategy_config: Dict[str, Any]) -> DataRequirement:
        """
        价值平均策略需要少量历史数据（判断趋势）和实时价格
        """
        return DataRequirement(
            history_days=30,
            needs_realtime_price=True
        )

    def _get_execution_count(self, strategy_config: Dict[str, Any]) -> int:
        """
        计算从起始日期到现在的执行次数

        Args:
            strategy_config: 策略配置

        Returns:
            执行次数
        """
        start_date_str = strategy_config.get("start_date")
        frequency = strategy_config.get("frequency", "monthly")

        if not start_date_str:
            return 1

        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            now = datetime.now()

            # 计算时间差（月数）
            months_diff = (now.year - start_date.year) * 12 + (now.month - start_date.month)

            if frequency == "monthly":
                return max(1, months_diff + 1)
            elif frequency == "weekly":
                weeks_diff = (now - start_date).days // 7
                return max(1, weeks_diff + 1)
            else:
                return 1

        except Exception as e:
            logger.error(f"计算执行次数失败: {e}")
            return 1
