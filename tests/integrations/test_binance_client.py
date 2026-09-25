"""Binance 客户端测试"""
import pytest
from unittest.mock import Mock, patch
from integrations.binance_client import BinanceClient

@pytest.fixture
def binance_client():
    """创建测试客户端"""
    return BinanceClient("test_api_key", "test_secret_key")

def test_get_realtime_price(binance_client):
    """测试获取实时价格"""
    with patch.object(binance_client, '_call_api') as mock_call:
        mock_call.return_value = {"price": "45.20"}

        price = binance_client.get_realtime_price("TQQQ")

        assert price == 45.20
        mock_call.assert_called_once()

def test_get_account_balance(binance_client):
    """测试获取账户余额"""
    with patch.object(binance_client, '_call_api') as mock_call:
        mock_call.return_value = {
            "balances": [
                {"asset": "USDT", "free": "10000.00", "locked": "0.00"}
            ]
        }

        balance = binance_client.get_account_balance()

        assert "USDT" in balance
        assert balance["USDT"]["free"] == 10000.0

def test_place_order(binance_client):
    """测试下单"""
    with patch.object(binance_client, '_call_api') as mock_call:
        mock_call.return_value = {
            "orderId": 12345,
            "executedQty": "2.5",
            "cummulativeQuoteQty": "113.00",
            "status": "FILLED"
        }

        result = binance_client.place_order("TQQQ", "BUY", 2.5)

        assert result["orderId"] == 12345
        assert result["executedQty"] == "2.5"

def test_rate_limiter_integrated(binance_client):
    """测试限流器集成"""
    # 限流器应该在初始化时创建
    assert binance_client.rate_limiter is not None

def test_place_order_validates_quantity(binance_client):
    """测试订单数量验证"""
    # 数量必须大于 0
    with pytest.raises(ValueError, match="订单数量必须大于 0"):
        binance_client.place_order("TQQQ", "BUY", 0)

    with pytest.raises(ValueError, match="订单数量必须大于 0"):
        binance_client.place_order("TQQQ", "BUY", -1.5)
