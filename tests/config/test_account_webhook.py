"""测试账户配置中的 webhook 文件加载功能"""
import pytest
import yaml
from pathlib import Path
from config.loader import ConfigLoader


def test_load_account_config_with_webhook_file(tmp_path):
    """测试从账户配置中加载 webhook 文件"""
    # 创建账户配置文件
    account_config = {
        "account": {
            "name": "test_account",
            "api_key_file": "secrets/test_account.key",
            "webhook_file": "secrets/test_account_webhook.txt",
            "initial_balance": 10000.0
        },
        "strategies": []
    }

    accounts_dir = tmp_path / "configs" / "accounts"
    accounts_dir.mkdir(parents=True)
    account_file = accounts_dir / "test_account.yaml"
    account_file.write_text(yaml.dump(account_config))

    # 创建密钥文件
    secrets_dir = tmp_path / "secrets"
    secrets_dir.mkdir()
    secret_file = secrets_dir / "test_account.key"
    secret_file.write_text("API_KEY: test_key\nAPI_SECRET: test_secret")

    # 创建 webhook 文件
    webhook_file = secrets_dir / "test_account_webhook.txt"
    webhook_file.write_text("# Test webhook\nhttps://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=test123\n")

    # 加载配置
    loader = ConfigLoader(
        base_path=str(tmp_path),
        accounts_path=str(accounts_dir),
        secrets_path=str(secrets_dir)
    )
    accounts = loader.load_account_configs()

    # 验证 webhook 已加载
    assert len(accounts) == 1
    assert "webhook" in accounts[0]["account"]
    assert accounts[0]["account"]["webhook"] == "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=test123"


def test_load_account_config_without_webhook_file(tmp_path):
    """测试账户配置没有指定 webhook 文件时正常加载"""
    account_config = {
        "account": {
            "name": "test_account",
            "api_key_file": "secrets/test_account.key",
            "initial_balance": 10000.0
        },
        "strategies": []
    }

    accounts_dir = tmp_path / "configs" / "accounts"
    accounts_dir.mkdir(parents=True)
    account_file = accounts_dir / "test_account.yaml"
    account_file.write_text(yaml.dump(account_config))

    secrets_dir = tmp_path / "secrets"
    secrets_dir.mkdir()
    secret_file = secrets_dir / "test_account.key"
    secret_file.write_text("API_KEY: test_key\nAPI_SECRET: test_secret")

    loader = ConfigLoader(
        base_path=str(tmp_path),
        accounts_path=str(accounts_dir),
        secrets_path=str(secrets_dir)
    )
    accounts = loader.load_account_configs()

    assert len(accounts) == 1
    assert "webhook" not in accounts[0]["account"]
