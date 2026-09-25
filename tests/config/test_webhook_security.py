"""测试 webhook 路径遍历攻击防护"""
import pytest
import yaml
from pathlib import Path
from config.loader import ConfigLoader


def test_webhook_path_traversal_attack(tmp_path):
    """测试路径遍历攻击被阻止"""
    # 创建系统配置，尝试使用路径遍历
    system_config = {
        "system": {"timezone": "America/New_York"},
        "notifications": {
            "admin_webhook_file": "../../etc/passwd"  # 路径遍历攻击
        }
    }

    system_file = tmp_path / "system.yaml"
    system_file.write_text(yaml.dump(system_config))

    # 创建 secrets 目录
    (tmp_path / "secrets").mkdir()

    loader = ConfigLoader(base_path=str(tmp_path))

    # 应该抛出 ValueError
    with pytest.raises(ValueError, match="Webhook 文件必须在 secrets 目录内"):
        loader.load_system_config()


def test_webhook_absolute_path_attack(tmp_path):
    """测试绝对路径攻击被阻止"""
    system_config = {
        "system": {"timezone": "America/New_York"},
        "notifications": {
            "admin_webhook_file": "/etc/passwd"  # 绝对路径攻击
        }
    }

    system_file = tmp_path / "system.yaml"
    system_file.write_text(yaml.dump(system_config))

    (tmp_path / "secrets").mkdir()

    loader = ConfigLoader(base_path=str(tmp_path))

    with pytest.raises(ValueError, match="Webhook 文件必须在 secrets 目录内"):
        loader.load_system_config()
