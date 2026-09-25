"""SQLite 数据库操作封装"""
import sqlite3
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import json

class Database:
    """数据库操作类"""

    def __init__(self, db_path: str = "data/trading.db"):
        """初始化数据库连接"""
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

    def init_db(self):
        """初始化数据库表"""
        cursor = self.conn.cursor()

        # 创建 trades 表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_name TEXT NOT NULL,
                strategy_id TEXT,
                symbol TEXT NOT NULL,
                action TEXT NOT NULL,
                quantity REAL NOT NULL,
                price REAL NOT NULL,
                amount REAL NOT NULL,
                fee REAL NOT NULL,
                trigger_reason TEXT NOT NULL,
                executed_at TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)

        # 创建 strategy_executions 表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS strategy_executions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy_id TEXT NOT NULL,
                account_name TEXT NOT NULL,
                executed_at TEXT NOT NULL,
                market_data_snapshot TEXT NOT NULL,
                calculation_result TEXT NOT NULL,
                signal TEXT NOT NULL,
                signal_amount REAL NOT NULL,
                trade_id INTEGER,
                status TEXT NOT NULL,
                error_message TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)

        # 创建 positions 表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_name TEXT NOT NULL,
                symbol TEXT NOT NULL,
                quantity REAL NOT NULL,
                avg_cost REAL NOT NULL,
                last_updated_at TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                UNIQUE(account_name, symbol)
            )
        """)

        # 创建 account_snapshots 表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS account_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_name TEXT NOT NULL,
                total_balance REAL NOT NULL,
                positions_snapshot TEXT NOT NULL,
                snapshot_type TEXT NOT NULL,
                snapshot_at TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)

        # 创建 notifications 表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                notification_type TEXT NOT NULL,
                recipient TEXT NOT NULL,
                content_summary TEXT NOT NULL,
                status TEXT NOT NULL,
                sent_at TEXT NOT NULL,
                error_message TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)

        self.conn.commit()

    def save_trade(self, trade_data: Dict[str, Any]) -> int:
        """保存交易记录"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO trades (
                account_name, strategy_id, symbol, action, quantity,
                price, amount, fee, trigger_reason, executed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            trade_data["account_name"],
            trade_data.get("strategy_id"),
            trade_data["symbol"],
            trade_data["action"],
            trade_data["quantity"],
            trade_data["price"],
            trade_data["amount"],
            trade_data["fee"],
            trade_data["trigger_reason"],
            trade_data["executed_at"]
        ))
        self.conn.commit()
        return cursor.lastrowid

    def save_strategy_execution(self, execution_data: Dict[str, Any]) -> int:
        """保存策略执行记录"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO strategy_executions (
                strategy_id, account_name, executed_at, market_data_snapshot,
                calculation_result, signal, signal_amount, trade_id, status, error_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            execution_data["strategy_id"],
            execution_data["account_name"],
            execution_data["executed_at"],
            execution_data["market_data_snapshot"],
            execution_data["calculation_result"],
            execution_data["signal"],
            execution_data["signal_amount"],
            execution_data.get("trade_id"),
            execution_data["status"],
            execution_data.get("error_message")
        ))
        self.conn.commit()
        return cursor.lastrowid

    def get_position(self, account_name: str, symbol: str) -> Optional[Dict[str, Any]]:
        """获取持仓"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM positions
            WHERE account_name = ? AND symbol = ?
        """, (account_name, symbol))

        row = cursor.fetchone()
        if row:
            return {
                "id": row["id"],
                "account_name": row["account_name"],
                "symbol": row["symbol"],
                "quantity": row["quantity"],
                "avg_cost": row["avg_cost"],
                "last_updated_at": row["last_updated_at"],
                "created_at": row["created_at"]
            }
        return None

    def update_position(self, account_name: str, symbol: str, position_data: Dict[str, Any]):
        """更新持仓（插入或更新）"""
        cursor = self.conn.cursor()
        now = datetime.now(timezone.utc).isoformat()

        cursor.execute("""
            INSERT INTO positions (account_name, symbol, quantity, avg_cost, last_updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(account_name, symbol)
            DO UPDATE SET
                quantity = excluded.quantity,
                avg_cost = excluded.avg_cost,
                last_updated_at = excluded.last_updated_at
        """, (
            account_name,
            symbol,
            position_data["quantity"],
            position_data["avg_cost"],
            now
        ))
        self.conn.commit()

    def save_account_snapshot(self, snapshot_data: Dict[str, Any]) -> int:
        """保存账户快照"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO account_snapshots (
                account_name, total_balance, positions_snapshot,
                snapshot_type, snapshot_at
            ) VALUES (?, ?, ?, ?, ?)
        """, (
            snapshot_data["account_name"],
            snapshot_data["total_balance"],
            snapshot_data["positions_snapshot"],
            snapshot_data["snapshot_type"],
            snapshot_data["snapshot_at"]
        ))
        self.conn.commit()
        return cursor.lastrowid

    def save_notification(self, notification_data: Dict[str, Any]) -> int:
        """保存通知记录"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO notifications (
                notification_type, recipient, content_summary,
                status, sent_at, error_message
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            notification_data["notification_type"],
            notification_data["recipient"],
            notification_data["content_summary"],
            notification_data["status"],
            notification_data["sent_at"],
            notification_data.get("error_message")
        ))
        self.conn.commit()
        return cursor.lastrowid

    def close(self):
        """关闭数据库连接"""
        self.conn.close()
