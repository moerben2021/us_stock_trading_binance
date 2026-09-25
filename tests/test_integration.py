"""集成测试"""
import pytest
from pathlib import Path
import sys
import sqlite3

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_imports():
    """测试所有模块可以正常导入"""
    # Import all major modules
    from config.loader import ConfigLoader
    from storage.database import Database
    from strategies.dca import DCAStrategy
    from strategies.drawdown import DrawdownStrategy
    from strategies.value_averaging import ValueAveragingStrategy
    from core.trade_executor import TradeExecutor
    from core.strategy_engine import StrategyEngine
    from core.scheduler import Scheduler

    # Assert each is not None
    assert ConfigLoader is not None
    assert Database is not None
    assert DCAStrategy is not None
    assert DrawdownStrategy is not None
    assert ValueAveragingStrategy is not None
    assert TradeExecutor is not None
    assert StrategyEngine is not None
    assert Scheduler is not None


def test_database_initialization():
    """测试数据库初始化"""
    # Create in-memory database
    from storage.database import Database

    db = Database(":memory:")

    # Initialize
    db.init_db()

    # Query sqlite_master for table names
    tables = db.conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()

    table_names = [table[0] for table in tables]

    # Verify tables exist
    assert "trades" in table_names, f"'trades' table not found. Tables: {table_names}"
    assert "strategy_executions" in table_names, f"'strategy_executions' table not found. Tables: {table_names}"
    assert "positions" in table_names, f"'positions' table not found. Tables: {table_names}"
