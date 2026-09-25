import pytest
import yaml
from pathlib import Path
from config.loader import ConfigLoader

@pytest.fixture
def config_loader(tmp_path):
    """创建测试配置加载器"""
    # 创建测试配置文件
    system_config = {
        "system": {"timezone": "America/New_York", "log_level": "INFO"},
        "database": {"path": "data/trading.db"}
    }

    system_file = tmp_path / "system.yaml"
    system_file.write_text(yaml.dump(system_config))

    # 创建账户配置
    accounts_dir = tmp_path / "accounts"
    accounts_dir.mkdir()

    account_config = {
        "account": {"name": "alice", "wecom_webhook": "https://example.com"},
        "strategies": [
            {"id": "alice_tqqq_dca", "type": "DCA", "symbol": "TQQQ", "config": {"base_amount": 100}}
        ]
    }

    account_file = accounts_dir / "alice.yaml"
    account_file.write_text(yaml.dump(account_config))

    # 创建密钥文件
    secrets_dir = tmp_path / "secrets"
    secrets_dir.mkdir()

    secret_config = {
        "binance": {"api_key": "test_key", "secret_key": "test_secret"}
    }

    secret_file = secrets_dir / "alice.key"
    secret_file.write_text(yaml.dump(secret_config))

    return ConfigLoader(str(tmp_path), str(accounts_dir), str(secrets_dir))

def test_load_system_config(config_loader):
    """测试加载系统配置"""
    config = config_loader.load_system_config()

    assert config["system"]["timezone"] == "America/New_York"
    assert config["database"]["path"] == "data/trading.db"

def test_load_account_configs(config_loader):
    """测试加载账户配置"""
    accounts = config_loader.load_account_configs()

    assert len(accounts) == 1
    assert accounts[0]["account"]["name"] == "alice"
    assert accounts[0]["binance"]["api_key"] == "test_key"
    assert len(accounts[0]["strategies"]) == 1
