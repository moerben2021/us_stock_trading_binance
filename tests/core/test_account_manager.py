"""Account Manager 单元测试"""
import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock
from core.account_manager import AccountManager


class TestAccountManager:
    """AccountManager 测试类"""

    @pytest.fixture
    def mock_database(self):
        """模拟数据库"""
        return Mock()

    @pytest.fixture
    def account_manager(self, mock_database):
        """创建 AccountManager 实例"""
        return AccountManager(mock_database)

    def test_create_account_snapshot(self, account_manager, mock_database):
        """测试创建账户快照"""
        # 安排：设置模拟数据库返回值
        mock_database.save_account_snapshot.return_value = 123

        # 执行：创建快照
        snapshot_data = {
            "account_name": "account1",
            "total_balance": 10000.0,
            "positions_snapshot": '{"BTC": 0.5}',
            "snapshot_type": "daily_close",
            "snapshot_at": "2024-01-01T09:00:00"
        }
        result = account_manager.create_account_snapshot(snapshot_data)

        # 断言：验证数据库被正确调用
        mock_database.save_account_snapshot.assert_called_once_with(snapshot_data)
        assert result == 123

    def test_get_account_summary(self, account_manager):
        """测试获取账户汇总"""
        # 安排：创建模拟 binance_client
        mock_binance_client = Mock()
        mock_binance_client.get_account_balance.return_value = {
            "total_balance": 15000.0,
            "available_balance": 5000.0
        }

        # 执行：获取账户汇总
        result = account_manager.get_account_summary("account1", mock_binance_client)

        # 断言：验证返回值包含必要字段
        assert "account_name" in result
        assert result["account_name"] == "account1"
        assert "total_balance" in result
        assert "available_balance" in result
        mock_binance_client.get_account_balance.assert_called_once()
