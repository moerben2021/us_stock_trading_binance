"""测试配置加载器的 webhook 文件加载功能"""
import pytest
import yaml
from pathlib import Path
from config.loader import ConfigLoader


def test_load_system_config_with_webhook_file(tmp_path):
    """测试从文件加载 webhook URL"""
    # 创建系统配置文件
    system_config = {
        "system": {"timezone": "America/New_York", "log_level": "INFO"},
        "database": {"path": "data/trading.db"},
        "notifications": {
            "admin_webhook_file": "secrets/wecom_webhook.txt",
            "summaries": {"daily": {"enabled": True, "time": "16:30"}}
        }
    }

    system_file = tmp_path / "system.yaml"
    system_file.write_text(yaml.dump(system_config))

    # 创建 webhook 文件
    webhook_file = tmp_path / "secrets" / "wecom_webhook.txt"
    webhook_file.parent.mkdir(parents=True)
    webhook_file.write_text("# 企业微信 Webhook\nhttps://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=test123\n")

    # 加载配置
    loader = ConfigLoader(base_path=str(tmp_path))
    config = loader.load_system_config()

    # 验证 webhook URL 已加载
    assert "admin_webhook" in config["notifications"]
    assert config["notifications"]["admin_webhook"] == "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=test123"


def test_load_system_config_webhook_file_not_found(tmp_path):
    """测试 webhook 文件不存在时抛出异常"""
    system_config = {
        "system": {"timezone": "America/New_York"},
        "notifications": {"admin_webhook_file": "secrets/wecom_webhook.txt"}
    }

    system_file = tmp_path / "system.yaml"
    system_file.write_text(yaml.dump(system_config))

    loader = ConfigLoader(base_path=str(tmp_path))

    with pytest.raises(FileNotFoundError, match="Webhook 文件不存在"):
        loader.load_system_config()


def test_load_system_config_without_webhook_file(tmp_path):
    """测试没有 webhook 文件配置时正常加载"""
    system_config = {
        "system": {"timezone": "America/New_York", "log_level": "INFO"},
        "database": {"path": "data/trading.db"}
    }

    system_file = tmp_path / "system.yaml"
    system_file.write_text(yaml.dump(system_config))

    loader = ConfigLoader(base_path=str(tmp_path))
    config = loader.load_system_config()

    assert "system" in config
    assert config["system"]["timezone"] == "America/New_York"
