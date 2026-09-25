# tests/integrations/test_market_data_service.py
import pytest
from unittest.mock import Mock, patch
from datetime import datetime
import pandas as pd
from integrations.market_data_service import MarketDataService

@pytest.fixture
def market_data_service():
    """创建市场数据服务"""
    yfinance_client = Mock()
    binance_client = Mock()
    return MarketDataService(yfinance_client, binance_client)

def test_get_market_data_with_cache(market_data_service):
    """测试获取市场数据（缓存）"""
    # Mock yFinance 数据
    mock_df = pd.DataFrame({
        'Close': [45.0, 46.0, 45.5],
        'Adj Close': [45.0, 46.0, 45.5],
        'High': [46.0, 47.0, 46.5],
        'Low': [44.0, 45.0, 45.0]
    })
    market_data_service.yfinance_client.get_history_data.return_value = mock_df
    market_data_service.binance_client.get_realtime_price.return_value = 45.20

    # 第一次调用
    data1 = market_data_service.get_market_data("TQQQ", 10)

    # 第二次调用应该使用缓存
    data2 = market_data_service.get_market_data("TQQQ", 10)

    # yFinance 只应该被调用一次
    assert market_data_service.yfinance_client.get_history_data.call_count == 1
    assert data1["current_price"] == 45.20
    assert data2["current_price"] == 45.20

def test_get_realtime_price_with_cache(market_data_service):
    """测试获取实时价格（缓存）"""
    market_data_service.binance_client.get_realtime_price.return_value = 45.20

    # 第一次调用
    price1 = market_data_service.get_realtime_price("TQQQ")

    # 第二次调用应该使用缓存
    price2 = market_data_service.get_realtime_price("TQQQ")

    # Binance 只应该被调用一次（缓存1分钟）
    assert market_data_service.binance_client.get_realtime_price.call_count == 1
    assert price1 == 45.20
    assert price2 == 45.20

def test_cache_clear_on_new_trading_day(market_data_service):
    """测试新交易日清空缓存"""
    mock_df = pd.DataFrame({
        'Close': [45.0],
        'Adj Close': [45.0],
        'High': [46.0],
        'Low': [44.0]
    })
    market_data_service.yfinance_client.get_history_data.return_value = mock_df
    market_data_service.binance_client.get_realtime_price.return_value = 45.20

    # 第一天
    with patch('integrations.market_data_service.get_us_trading_day', return_value="2026-09-24"):
        data1 = market_data_service.get_market_data("TQQQ", 10)

    # 第二天（新交易日）
    with patch('integrations.market_data_service.get_us_trading_day', return_value="2026-09-25"):
        data2 = market_data_service.get_market_data("TQQQ", 10)

    # yFinance 应该被调用两次（缓存已清空）
    assert market_data_service.yfinance_client.get_history_data.call_count == 2
