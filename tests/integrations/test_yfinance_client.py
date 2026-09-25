"""yFinance 客户端测试"""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
from integrations.yfinance_client import YFinanceClient


def test_yfinance_client_get_history_data():
    """测试获取历史数据"""
    client = YFinanceClient()

    # 创建模拟数据
    mock_data = pd.DataFrame({
        'Open': [150.0, 151.0, 152.0],
        'High': [155.0, 156.0, 157.0],
        'Low': [149.0, 150.0, 151.0],
        'Close': [154.0, 155.0, 156.0],
        'Adj Close': [153.5, 154.5, 155.5],
        'Volume': [1000000, 1100000, 1200000]
    }, index=pd.date_range('2026-09-23', periods=3))

    # Mock yfinance Ticker
    with patch('integrations.yfinance_client.yf.Ticker') as mock_ticker:
        mock_instance = MagicMock()
        mock_instance.history.return_value = mock_data
        mock_ticker.return_value = mock_instance

        # 获取 AAPL 最近 10 天的数据
        data = client.get_history_data("AAPL", 10)

        assert data is not None
        assert len(data) > 0
        assert "Adj Close" in data.columns
        assert "Volume" in data.columns

        # 验证 yfinance 被正确调用
        mock_ticker.assert_called_once_with("AAPL")
        mock_instance.history.assert_called_once()


def test_yfinance_client_get_history_data_empty():
    """测试获取历史数据为空的情况"""
    client = YFinanceClient()

    # 创建空的 DataFrame
    mock_data = pd.DataFrame()

    with patch('integrations.yfinance_client.yf.Ticker') as mock_ticker:
        mock_instance = MagicMock()
        mock_instance.history.return_value = mock_data
        mock_ticker.return_value = mock_instance

        # 获取不存在的股票数据
        data = client.get_history_data("INVALID", 10)

        assert data is not None
        assert len(data) == 0


def test_yfinance_client_is_trading_day():
    """测试判断交易日"""
    client = YFinanceClient()

    # Mock utils.date_utils.is_trading_day
    with patch('integrations.yfinance_client.utils_is_trading_day') as mock_is_trading_day:
        # 2026-09-28 是周一，应该是交易日
        mock_is_trading_day.return_value = True
        result = client.is_trading_day(datetime(2026, 9, 28))
        assert result == True
        mock_is_trading_day.assert_called_once_with(datetime(2026, 9, 28))

        # 重置 mock
        mock_is_trading_day.reset_mock()

        # 2026-09-26 是周六，不是交易日
        mock_is_trading_day.return_value = False
        result = client.is_trading_day(datetime(2026, 9, 26))
        assert result == False
        mock_is_trading_day.assert_called_once_with(datetime(2026, 9, 26))
