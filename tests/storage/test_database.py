import pytest
import sqlite3
from datetime import datetime, timezone
from storage.database import Database

@pytest.fixture
def db():
    """创建测试数据库"""
    db = Database(":memory:")
    db.init_db()
    return db

def test_init_db_creates_tables(db):
    """测试初始化创建所有表"""
    conn = db.conn
    cursor = conn.cursor()

    # 检查表是否存在
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cursor.fetchall()}

    assert "trades" in tables
    assert "strategy_executions" in tables
    assert "positions" in tables
    assert "account_snapshots" in tables
    assert "notifications" in tables

def test_save_trade(db):
    """测试保存交易记录"""
    trade_data = {
        "account_name": "alice",
        "strategy_id": "alice_tqqq_dca",
        "symbol": "TQQQ",
        "action": "BUY",
        "quantity": 2.5,
        "price": 45.20,
        "amount": 113.00,
        "fee": 0.50,
        "trigger_reason": "strategy_auto",
        "executed_at": datetime.now(timezone.utc).isoformat()
    }

    trade_id = db.save_trade(trade_data)
    assert trade_id > 0

    # 验证保存的数据
    cursor = db.conn.cursor()
    cursor.execute("SELECT * FROM trades WHERE id = ?", (trade_id,))
    row = cursor.fetchone()

    assert row[1] == "alice"  # account_name
    assert row[3] == "TQQQ"   # symbol
    assert row[4] == "BUY"    # action

def test_get_position(db):
    """测试获取持仓"""
    # 先插入持仓数据
    position_data = {
        "account_name": "alice",
        "symbol": "TQQQ",
        "quantity": 10.0,
        "avg_cost": 42.50
    }
    db.update_position("alice", "TQQQ", position_data)

    # 获取持仓
    position = db.get_position("alice", "TQQQ")

    assert position is not None
    assert position["quantity"] == 10.0
    assert position["avg_cost"] == 42.50

def test_update_position(db):
    """测试更新持仓"""
    position_data = {
        "account_name": "alice",
        "symbol": "TQQQ",
        "quantity": 10.0,
        "avg_cost": 42.50
    }

    db.update_position("alice", "TQQQ", position_data)

    # 更新持仓
    updated_data = {
        "account_name": "alice",
        "symbol": "TQQQ",
        "quantity": 12.5,
        "avg_cost": 43.20
    }
    db.update_position("alice", "TQQQ", updated_data)

    # 验证更新
    position = db.get_position("alice", "TQQQ")
    assert position["quantity"] == 12.5
    assert position["avg_cost"] == 43.20
