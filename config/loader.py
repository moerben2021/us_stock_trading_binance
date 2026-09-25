"""配置加载器"""
import os
import yaml
from typing import Dict, List, Any
from pathlib import Path

class ConfigLoader:
    """配置加载器"""

    def __init__(self, base_path: str = ".", accounts_path: str = "configs/accounts", secrets_path: str = "secrets"):
        """
        初始化配置加载器

        Args:
            base_path: 配置基础路径
            accounts_path: 账户配置目录路径
            secrets_path: 密钥目录路径
        """
        self.base_path = Path(base_path)
        self.accounts_path = Path(accounts_path)
        self.secrets_path = Path(secrets_path)

    def load_system_config(self) -> Dict[str, Any]:
        """
        加载系统配置

        Returns:
            系统配置字典
        """
        system_file = self.base_path / "system.yaml"

        if not system_file.exists():
            raise FileNotFoundError(f"系统配置文件不存在: {system_file}")

        with open(system_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        return config

    def load_account_configs(self) -> List[Dict[str, Any]]:
        """
        加载所有账户配置

        Returns:
            账户配置列表，每个配置包含业务配置和密钥信息
        """
        accounts = []

        if not self.accounts_path.exists():
            return accounts

        # 遍历账户配置目录
        for account_file in self.accounts_path.glob("*.yaml"):
            # 加载业务配置
            with open(account_file, 'r', encoding='utf-8') as f:
                account_config = yaml.safe_load(f)

            # 加载对应的密钥文件
            account_name = account_config["account"]["name"]
            secret_file = self.secrets_path / f"{account_name}.key"

            if secret_file.exists():
                with open(secret_file, 'r', encoding='utf-8') as f:
                    secret_config = yaml.safe_load(f)

                # 合并配置
                account_config.update(secret_config)
            else:
                raise FileNotFoundError(f"账户 {account_name} 的密钥文件不存在: {secret_file}")

            accounts.append(account_config)

        return accounts

    def load_manual_trade_configs(self) -> List[Dict[str, Any]]:
        """
        加载手动交易配置

        Returns:
            手动交易配置列表
        """
        manual_trades = []
        manual_trades_path = self.base_path / "configs" / "manual_trades"

        if not manual_trades_path.exists():
            return manual_trades

        # 只加载 .yaml 文件，忽略 .processing 和 .failed
        for trade_file in manual_trades_path.glob("*.yaml"):
            if trade_file.stem.startswith("executed_"):
                continue

            with open(trade_file, 'r', encoding='utf-8') as f:
                trade_config = yaml.safe_load(f)

            trade_config["_file_path"] = str(trade_file)
            manual_trades.append(trade_config)

        return manual_trades
