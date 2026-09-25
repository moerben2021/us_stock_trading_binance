"""Scheduler 单元测试"""
import pytest
import signal
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch
from core.scheduler import Scheduler


class TestScheduler:
    """Scheduler 测试类"""

    @pytest.fixture
    def mock_config_loader(self):
        """模拟配置加载器"""
        return Mock()

    @pytest.fixture
    def mock_strategy_engine(self):
        """模拟策略引擎"""
        return Mock()

    @pytest.fixture
    def system_config(self):
        """系统配置"""
        return {
            "scheduler": {
                "manual_trade_scan_interval": 60
            }
        }

    @pytest.fixture
    def scheduler(self, mock_config_loader, mock_strategy_engine, system_config):
        """创建 Scheduler 实例"""
        return Scheduler(mock_config_loader, mock_strategy_engine, system_config)

    def test_scheduler_initialization(self, scheduler, system_config):
        """测试调度器初始化"""
        # 断言：验证调度器已初始化并存储了配置
        assert scheduler.system_config == system_config
        assert scheduler.scheduler is not None
        assert scheduler.config_loader is not None
        assert scheduler.strategy_engine is not None

    def test_scheduler_stores_config(self, scheduler, system_config):
        """测试调度器存储配置"""
        # 断言：验证 system_config 被正确存储
        assert scheduler.system_config.get("scheduler") is not None
        assert scheduler.system_config["scheduler"].get("manual_trade_scan_interval") == 60
