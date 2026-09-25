"""数据模型定义"""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class TradeRecord:
    """交易记录"""
    account_name: str
    symbol: str
    action: str  # BUY / SELL
    quantity: float
    price: float
    amount: float
    fee: float
    trigger_reason: str  # strategy_auto / manual / sell_rule
    executed_at: str
    strategy_id: Optional[str] = None
    id: Optional[int] = None
    created_at: Optional[str] = None

@dataclass
class StrategyExecution:
    """策略执行记录"""
    strategy_id: str
    account_name: str
    executed_at: str
    market_data_snapshot: str  # JSON
    calculation_result: str  # JSON
    signal: str  # BUY / SELL / HOLD
    signal_amount: float
    status: str  # success / failed / skipped
    trade_id: Optional[int] = None
    error_message: Optional[str] = None
    id: Optional[int] = None
    created_at: Optional[str] = None

@dataclass
class Position:
    """持仓"""
    account_name: str
    symbol: str
    quantity: float
    avg_cost: float
    last_updated_at: str
    id: Optional[int] = None
    created_at: Optional[str] = None

@dataclass
class AccountSnapshot:
    """账户快照"""
    account_name: str
    total_balance: float
    positions_snapshot: str  # JSON
    snapshot_type: str  # after_trade / daily_close / weekly_summary / monthly_summary
    snapshot_at: str
    id: Optional[int] = None
    created_at: Optional[str] = None

@dataclass
class Notification:
    """通知记录"""
    notification_type: str  # trade / daily_summary / weekly_summary / alert
    recipient: str
    content_summary: str
    status: str  # sent / failed
    sent_at: str
    error_message: Optional[str] = None
    id: Optional[int] = None
    created_at: Optional[str] = None
