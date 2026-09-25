import pytest
from unittest.mock import Mock, patch
from integrations.wecom_notifier import WeComNotifier

@pytest.fixture
def notifier():
    """创建通知器"""
    return WeComNotifier()

def test_send_trade_notification(notifier):
    """测试发送交易通知"""
    with patch('requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"errcode": 0}

        trade_info = {
            "account_name": "alice",
            "strategy_id": "alice_tqqq_dca",
            "strategy_type": "DCA",
            "symbol": "TQQQ",
            "action": "BUY",
            "quantity": 2.5,
            "price": 45.20,
            "amount": 113.00,
            "fee": 0.50,
            "balance_before": 8500.00,
            "balance_after": 8386.50
        }

        result = notifier.send_trade_notification("https://example.com/webhook", trade_info)

        assert result is True
        mock_post.assert_called_once()

def test_send_alert_notification(notifier):
    """测试发送告警通知"""
    with patch('requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"errcode": 0}

        alert_info = {
            "alert_type": "trade_failed",
            "message": "交易执行失败",
            "details": "余额不足"
        }

        result = notifier.send_alert_notification("https://example.com/webhook", alert_info)

        assert result is True

def test_send_summary_notification(notifier):
    """测试发送汇总通知"""
    with patch('requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"errcode": 0}

        summary_info = {
            "account_name": "alice",
            "period": "daily",
            "date": "2026-09-24",
            "trades_count": 2,
            "total_amount": 352.50,
            "positions": [
                {"symbol": "TQQQ", "quantity": 15.3, "cost": 42.50, "price": 45.20, "profit_pct": 6.35}
            ]
        }

        result = notifier.send_summary_notification("https://example.com/webhook", summary_info)

        assert result is True
