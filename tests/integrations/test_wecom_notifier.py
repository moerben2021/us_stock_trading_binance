import pytest
import requests
from unittest.mock import Mock, patch, call
from integrations.wecom_notifier import WeComNotifier

@pytest.fixture
def notifier():
    """创建通知器"""
    return WeComNotifier()

def test_send_trade_notification(notifier):
    """测试发送交易通知"""
    with patch('integrations.wecom_notifier.requests.post') as mock_post:
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

        # 验证 payload 内容
        call_args = mock_post.call_args
        assert call_args[0][0] == "https://example.com/webhook"
        payload = call_args[1]['json']
        assert payload['msgtype'] == 'text'
        assert 'text' in payload
        content = payload['text']['content']
        assert 'alice' in content
        assert 'alice_tqqq_dca' in content
        assert 'TQQQ' in content
        assert '买入' in content
        assert '2.5' in content
        assert 'UTC' in content

def test_send_alert_notification(notifier):
    """测试发送告警通知"""
    with patch('integrations.wecom_notifier.requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"errcode": 0}

        alert_info = {
            "alert_type": "trade_failed",
            "message": "交易执行失败",
            "details": "余额不足"
        }

        result = notifier.send_alert_notification("https://example.com/webhook", alert_info)

        assert result is True

        # 验证 payload 内容
        call_args = mock_post.call_args
        payload = call_args[1]['json']
        assert payload['msgtype'] == 'text'
        content = payload['text']['content']
        assert 'trade_failed' in content
        assert '交易执行失败' in content
        assert '余额不足' in content
        assert 'UTC' in content

def test_send_summary_notification(notifier):
    """测试发送汇总通知"""
    with patch('integrations.wecom_notifier.requests.post') as mock_post:
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

        # 验证 payload 内容
        call_args = mock_post.call_args
        payload = call_args[1]['json']
        assert payload['msgtype'] == 'text'
        content = payload['text']['content']
        assert 'alice' in content
        assert '每日汇总' in content
        assert '2026-09-24' in content
        assert 'TQQQ' in content
        assert '15.3' in content

def test_send_trade_notification_with_retry_on_network_error(notifier):
    """测试网络错误时的重试机制"""
    with patch('integrations.wecom_notifier.requests.post') as mock_post:
        # 前两次失败，第三次成功
        mock_post.side_effect = [
            requests.exceptions.ConnectionError("网络连接失败"),
            requests.exceptions.Timeout("请求超时"),
            Mock(status_code=200, json=lambda: {"errcode": 0})
        ]

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
        assert mock_post.call_count == 3

def test_send_alert_notification_with_retry_failure(notifier):
    """测试重试全部失败的情况"""
    with patch('integrations.wecom_notifier.requests.post') as mock_post:
        # 所有尝试都失败
        mock_post.side_effect = requests.exceptions.ConnectionError("网络连接失败")

        alert_info = {
            "alert_type": "trade_failed",
            "message": "交易执行失败",
            "details": "余额不足"
        }

        with pytest.raises(requests.exceptions.ConnectionError):
            notifier.send_alert_notification("https://example.com/webhook", alert_info)

        assert mock_post.call_count == 3

def test_send_notification_with_non_zero_errcode(notifier):
    """测试企业微信返回错误码的情况"""
    with patch('integrations.wecom_notifier.requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"errcode": 40001, "errmsg": "invalid credential"}

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

        assert result is False

def test_send_notification_with_http_error(notifier):
    """测试 HTTP 错误响应"""
    with patch('integrations.wecom_notifier.requests.post') as mock_post:
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("500 Server Error")
        mock_post.return_value = mock_response

        alert_info = {
            "alert_type": "trade_failed",
            "message": "交易执行失败",
            "details": "余额不足"
        }

        with pytest.raises(requests.exceptions.HTTPError):
            notifier.send_alert_notification("https://example.com/webhook", alert_info)

        assert mock_post.call_count == 3
