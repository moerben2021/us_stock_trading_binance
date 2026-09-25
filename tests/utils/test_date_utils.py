import pytest
from datetime import datetime
from utils.date_utils import is_trading_day, get_next_trading_day, get_us_trading_day

def test_is_trading_day_weekday():
    """测试工作日是交易日"""
    # 2026-09-28 是周一
    date = datetime(2026, 9, 28)
    assert is_trading_day(date) == True

def test_is_trading_day_weekend():
    """测试周末不是交易日"""
    # 2026-09-26 是周六
    date = datetime(2026, 9, 26)
    assert is_trading_day(date) == False

def test_get_next_trading_day():
    """测试获取下一个交易日"""
    # 从周五获取下一个交易日（应该是下周一）
    friday = datetime(2026, 9, 25)
    next_day = get_next_trading_day(friday)

    # 下一个交易日应该是周一
    assert next_day.weekday() == 0  # Monday

def test_get_us_trading_day():
    """测试获取美东时间的交易日"""
    date = get_us_trading_day()
    assert isinstance(date, str)
