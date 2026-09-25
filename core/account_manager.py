"""账户管理器"""
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class AccountManager:
    """账户管理器 - 管理账户快照和信息"""

    def __init__(self, database):
        """
        初始化账户管理器

        Args:
            database: 数据库实例
        """
        self.database = database
        logger.info("账户管理器初始化完成")

    def create_account_snapshot(self, snapshot_data: Dict[str, Any]) -> int:
        """
        创建账户快照

        Args:
            snapshot_data: 快照数据，包含：
                - account_name: 账户名
                - total_balance: 总余额
                - positions_snapshot: 持仓快照（JSON）
                - snapshot_type: 快照类型（daily_close、manual 等）
                - snapshot_at: 快照时间（UTC ISO 格式）

        Returns:
            快照 ID
        """
        try:
            snapshot_id = self.database.save_account_snapshot(snapshot_data)
            logger.info(
                f"账户快照创建成功: {snapshot_data['account_name']}, "
                f"snapshot_id={snapshot_id}, type={snapshot_data['snapshot_type']}"
            )
            return snapshot_id
        except Exception as e:
            logger.error(f"创建账户快照失败: {e}", exc_info=True)
            raise

    def get_account_summary(self, account_name: str, binance_client) -> Dict[str, Any]:
        """
        获取账户汇总信息

        Args:
            account_name: 账户名称
            binance_client: Binance 客户端

        Returns:
            账户汇总字典，包含余额和持仓信息
        """
        try:
            # 获取账户余额
            balance_info = binance_client.get_account_balance()

            summary = {
                "account_name": account_name,
                "total_balance": balance_info.get("total_balance", 0),
                "available_balance": balance_info.get("available_balance", 0),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            logger.info(f"账户汇总获取成功: {account_name}, 总余额={summary['total_balance']}")
            return summary
        except Exception as e:
            logger.error(f"获取账户汇总失败: {e}", exc_info=True)
            raise
