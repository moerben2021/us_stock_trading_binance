"""企业微信通知服务"""
import requests
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from utils.retry import retry_with_config, RetryConfig

logger = logging.getLogger(__name__)

class WeComNotifier:
    """企业微信通知器"""

    def __init__(self, database=None):
        """
        初始化企业微信通知器

        Args:
            database: 数据库实例（可选，用于记录通知历史）
        """
        self.database = database

    @retry_with_config(RetryConfig(max_attempts=3, interval_seconds=1.0, backoff='fixed'))
    def send_trade_notification(self, webhook_url: str, trade_info: Dict[str, Any]) -> bool:
        """
        发送交易通知

        Args:
            webhook_url: 企业微信 Webhook URL
            trade_info: 交易信息

        Returns:
            是否发送成功
        """
        action_cn = "买入" if trade_info["action"] == "BUY" else "卖出"

        # 检查是否为未成交状态
        status = trade_info.get("status", "completed")
        is_pending = (status == "pending")

        # 根据状态设置标题
        if is_pending:
            title = f"【交易通知 - {trade_info['account_name']} - 待成交】"
        else:
            title = f"【交易通知 - {trade_info['account_name']}】"

        content = f"""{title}
策略：{trade_info['strategy_id']} ({trade_info['strategy_type']})
标的：{trade_info['symbol']}
操作：{action_cn}
数量：{trade_info['quantity']}股
价格：${trade_info['price']}
金额：${trade_info['amount']}
手续费：${trade_info['fee']}
账户余额：${trade_info['balance_before']} → ${trade_info['balance_after']}"""

        # 如果是未成交状态，添加额外信息
        if is_pending:
            order_id = trade_info.get("order_id", "N/A")
            order_status = trade_info.get("order_status", "UNKNOWN")
            reason = trade_info.get("reason", "等待市场开盘")
            content += f"""

📌 状态：待成交
订单ID：{order_id}
订单状态：{order_status}
原因：{reason}"""
        else:
            content += f"""

✅ 状态：已成交"""

        content += f"""
时间：{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC"""

        success = self._send_message(webhook_url, content)

        # 记录通知到数据库
        if self.database and success:
            notification_type = "trade_pending" if is_pending else "trade"
            self.database.save_notification({
                "account_name": trade_info.get("account_name"),
                "notification_type": notification_type,
                "content": content,
                "sent_at": datetime.now(timezone.utc).isoformat(),
                "status": "success"
            })

        return success

    @retry_with_config(RetryConfig(max_attempts=3, interval_seconds=1.0, backoff='fixed'))
    def send_alert_notification(self, webhook_url: str, alert_info: Dict[str, Any]) -> bool:
        """
        发送告警通知

        Args:
            webhook_url: 企业微信 Webhook URL
            alert_info: 告警信息

        Returns:
            是否发送成功
        """
        content = f"""⚠️ 【系统告警】
类型：{alert_info['alert_type']}
消息：{alert_info['message']}
详情：{alert_info.get('details', '无')}
时间：{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC"""

        success = self._send_message(webhook_url, content)

        # 记录通知到数据库
        if self.database and success:
            self.database.save_notification({
                "account_name": alert_info.get("account_name", "system"),
                "notification_type": "alert",
                "content": content,
                "sent_at": datetime.now(timezone.utc).isoformat(),
                "status": "success"
            })

        return success

    @retry_with_config(RetryConfig(max_attempts=3, interval_seconds=1.0, backoff='fixed'))
    def send_summary_notification(self, webhook_url: str, summary_info: Dict[str, Any]) -> bool:
        """
        发送汇总通知

        Args:
            webhook_url: 企业微信 Webhook URL
            summary_info: 汇总信息

        Returns:
            是否发送成功
        """
        period_cn = {"daily": "每日", "weekly": "每周", "monthly": "每月"}.get(
            summary_info.get("period", "daily"), "汇总"
        )

        content = f"""【{period_cn}汇总 - {summary_info.get('account_name', '系统')}】
时间范围：{summary_info.get('date', 'N/A')}

📊 交易情况：
• 交易笔数：{summary_info.get('trades_count', 0)}笔
• 总交易金额：${summary_info.get('total_amount', 0):.2f}

📈 持仓情况："""

        for pos in summary_info.get("positions", []):
            profit_sign = "+" if pos.get("profit_pct", 0) >= 0 else ""
            content += f"\n• {pos['symbol']}：{pos['quantity']}股，成本${pos['cost']:.2f}，现价${pos['price']:.2f}，盈亏{profit_sign}{pos['profit_pct']:.2f}%"

        content += f"\n\n✅ 系统状态：正常运行"

        success = self._send_message(webhook_url, content)

        # 记录通知到数据库
        if self.database and success:
            self.database.save_notification({
                "account_name": summary_info.get("account_name", "system"),
                "notification_type": "summary",
                "content": content,
                "sent_at": datetime.now(timezone.utc).isoformat(),
                "status": "success"
            })

        return success

    def _send_message(self, webhook_url: str, content: str) -> bool:
        """
        发送消息到企业微信

        Args:
            webhook_url: Webhook URL
            content: 消息内容

        Returns:
            是否发送成功

        Raises:
            Exception: 网络请求失败时抛出异常供重试装饰器处理
        """
        payload = {
            "msgtype": "text",
            "text": {
                "content": content
            }
        }

        response = requests.post(webhook_url, json=payload, timeout=10)
        response.raise_for_status()

        result = response.json()
        if result.get("errcode") == 0:
            logger.info("企业微信通知发送成功")
            return True
        else:
            error_msg = f"企业微信通知发送失败: {result}"
            logger.error(error_msg)
            return False
