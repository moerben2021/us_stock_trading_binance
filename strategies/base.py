# strategies/base.py
"""策略基类"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass
class TradeSignal:
    """交易信号"""
    action: str  # "BUY" / "SELL" / "HOLD"
    amount: float  # 金额或数量
    reason: str  # 触发原因
    quantity: Optional[float] = None  # 可选：具体数量

@dataclass
class DataRequirement:
    """数据需求"""
    history_days: int = 0  # 需要的历史天数
    needs_realtime_price: bool = True  # 是否需要实时价格

class BaseStrategy(ABC):
    """策略基类"""

    @abstractmethod
    def calculate(
        self,
        account_config: Dict[str, Any],
        strategy_config: Dict[str, Any],
        market_data: Dict[str, Any],
        position: Optional[Dict[str, Any]]
    ) -> TradeSignal:
        """
        计算交易信号

        Args:
            account_config: 账户配置
            strategy_config: 策略实例配置
            market_data: 市场数据（历史行情 + 实时价格）
            position: 当前持仓（从 Binance API 同步）

        Returns:
            TradeSignal: 交易信号
        """
        pass

    @abstractmethod
    def get_required_data(self, strategy_config: Dict[str, Any]) -> DataRequirement:
        """
        声明策略所需的数据

        Args:
            strategy_config: 策略配置

        Returns:
            DataRequirement: 数据需求
        """
        pass

    def check_sell_rules(
        self,
        strategy_config: Dict[str, Any],
        position: Optional[Dict[str, Any]],
        current_price: float
    ) -> Optional[TradeSignal]:
        """
        检查通用卖出规则

        Args:
            strategy_config: 策略配置
            position: 当前持仓
            current_price: 当前价格

        Returns:
            如果触发卖出规则，返回 SELL 信号；否则返回 None
        """
        if not position or position.get("quantity", 0) <= 0:
            return None

        sell_rules = strategy_config.get("sell_rules", [])

        for rule in sell_rules:
            if rule["type"] == "profit_percentage":
                # 盈利百分比触发
                avg_cost = position.get("avg_cost", 0)
                if avg_cost > 0:
                    profit_pct = (current_price - avg_cost) / avg_cost * 100

                    if profit_pct >= rule["threshold"]:
                        # 计算卖出数量
                        quantity = position["quantity"]
                        sell_amount = 0

                        if rule["sell_type"] == "position_percentage":
                            sell_amount = quantity * rule["sell_amount"] / 100
                        elif rule["sell_type"] == "position_value":
                            sell_amount = rule["sell_amount"] / current_price
                        elif rule["sell_type"] == "profit_value":
                            profit_value = (current_price - avg_cost) * quantity
                            sell_amount = (rule["sell_amount"] / current_price) if profit_value > 0 else 0

                        if sell_amount > 0:
                            return TradeSignal(
                                action="SELL",
                                amount=sell_amount,
                                quantity=sell_amount,
                                reason=f"触发卖出规则: 盈利 {profit_pct:.2f}% >= {rule['threshold']}%"
                            )

        return None
