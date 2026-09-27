"""交易执行器"""
import logging
from typing import Dict, Any
from datetime import datetime, timezone
from strategies.base import TradeSignal
from utils.retry import retry_with_config, RetryConfig

logger = logging.getLogger(__name__)

class TradeExecutor:
    """
    交易执行器
    负责实际的交易执行、余额检查、重试和通知
    """

    # 交易手续费率（0.1%）
    FEE_RATE = 0.001

    def __init__(self, binance_client, database, notifier, system_config: Dict[str, Any]):
        """
        初始化交易执行器

        Args:
            binance_client: Binance 客户端
            database: 数据库
            notifier: 通知器
            system_config: 系统配置
        """
        self.binance_client = binance_client
        self.database = database
        self.notifier = notifier
        self.system_config = system_config

        # 重试配置
        retry_config = system_config.get("retry", {}).get("trade_execution", {})
        self.retry_config = RetryConfig(
            max_attempts=retry_config.get("max_attempts", 3),
            interval_seconds=retry_config.get("interval_seconds", 10),
            backoff=retry_config.get("backoff", "fixed")
        )

    def execute_trade(
        self,
        account_name: str,
        strategy_id: str,
        signal: TradeSignal,
        symbol: str,
        account_webhook: str = None
    ) -> Dict[str, Any]:
        """
        执行交易

        Args:
            account_name: 账户名称
            strategy_id: 策略 ID
            signal: 交易信号
            symbol: 标的代码
            account_webhook: 账户企业微信 Webhook

        Returns:
            执行结果字典
        """
        if signal.action == "HOLD":
            logger.info(f"策略 {strategy_id} 返回 HOLD，不执行交易")
            return {"success": True, "action": "HOLD"}

        try:
            if signal.action == "BUY":
                return self._execute_buy(account_name, strategy_id, signal, symbol, account_webhook)
            elif signal.action == "SELL":
                return self._execute_sell(account_name, strategy_id, signal, symbol, account_webhook)
            else:
                logger.error(f"未知的交易动作: {signal.action}")
                return {"success": False, "error": f"未知的交易动作: {signal.action}"}

        except Exception as e:
            logger.error(f"交易执行异常: {e}")

            # 发送告警通知
            if account_webhook:
                self.notifier.send_alert_notification(account_webhook, {
                    "alert_type": "trade_execution_failed",
                    "message": "交易执行失败",
                    "details": str(e)
                })

            return {"success": False, "error": str(e)}

    def _execute_buy(
        self,
        account_name: str,
        strategy_id: str,
        signal: TradeSignal,
        symbol: str,
        account_webhook: str
    ) -> Dict[str, Any]:
        """执行买入交易"""
        # 获取账户余额
        balance = self.binance_client.get_account_balance()
        # 美股交易使用 USDC
        usdt_balance = balance.get("USDC", {}).get("free", 0)

        # 检查余额
        required_amount = signal.amount

        if usdt_balance < required_amount:
            insufficient_action = self.system_config.get("balance_check", {}).get("insufficient_action", "partial")

            if insufficient_action == "skip":
                logger.warning(f"余额不足: 需要 ${required_amount}, 可用 ${usdt_balance}，跳过交易")

                # 发送告警
                if account_webhook:
                    self.notifier.send_alert_notification(account_webhook, {
                        "alert_type": "insufficient_balance",
                        "message": "余额不足，跳过交易",
                        "details": f"需要 ${required_amount:.2f}, 可用 ${usdt_balance:.2f}"
                    })

                return {"success": False, "error": "余额不足，已跳过"}
            else:
                # 部分执行
                logger.warning(f"余额不足: 需要 ${required_amount}, 可用 ${usdt_balance}，按实际余额执行")
                required_amount = usdt_balance

        # 获取实时价格
        current_price = self.binance_client.get_realtime_price(symbol)

        # 对于市价买单，直接传入金额（notional），不需要计算数量
        # Binance 美股 API 会自动计算能买到的股数

        # 执行下单（带重试）- 市价买单传入金额
        order_result = self._place_order_with_retry(symbol, "BUY", required_amount)

        # 获取订单ID
        order_id = order_result.get("orderId")

        # 下单接口返回的 status 只是请求确认码（S=已接受，F=失败）
        # 需要查询订单详情获取真实的成交情况
        if order_id:
            try:
                order_detail = self.binance_client.get_order_detail(order_id)
                executed_qty = float(order_detail.get("executedQty", 0))
                executed_amount = float(order_detail.get("cummulativeQuoteQty", 0))
                order_status = order_detail.get("status", "UNKNOWN")

                logger.info(f"订单详情: orderId={order_id}, status={order_status}, executedQty={executed_qty}, executedAmount={executed_amount}")

                # 如果未成交（周末或市场关闭），不继续后续流程
                if executed_qty == 0:
                    logger.warning(f"订单已提交但未成交: orderId={order_id}, status={order_status}（可能是市场关闭）")

                    # 发送未成交通知（保持交易通知的格式，但标注未成交状态）
                    if account_webhook:
                        # 获取当前余额
                        balance = self.binance_client.get_account_balance()
                        usdt_balance = balance.get("USDC", {}).get("free", 0)

                        self.notifier.send_trade_notification(account_webhook, {
                            "account_name": account_name,
                            "strategy_id": strategy_id,
                            "strategy_type": "N/A",
                            "symbol": symbol,
                            "action": "BUY",
                            "quantity": 0,  # 未成交
                            "price": current_price,
                            "amount": required_amount,  # 预期金额
                            "fee": 0,
                            "balance_before": usdt_balance,
                            "balance_after": usdt_balance,  # 余额未变化
                            "status": "pending",  # 标记为待成交
                            "order_id": order_id,
                            "order_status": order_status,
                            "reason": "市场关闭，订单已提交等待成交"
                        })

                    return {
                        "success": True,
                        "order_id": order_id,
                        "status": "pending",
                        "message": "订单已提交但未成交，等待市场开盘"
                    }

            except Exception as e:
                logger.error(f"查询订单详情失败: {e}，使用下单响应的默认值")
                # 如果查询失败，使用下单响应中的默认值（可能为0）
                executed_qty = float(order_result.get("executedQty", 0))
                executed_amount = float(order_result.get("cummulativeQuoteQty", 0))
        else:
            # 没有订单ID，使用下单响应中的值
            executed_qty = float(order_result.get("executedQty", 0))
            executed_amount = float(order_result.get("cummulativeQuoteQty", 0))

        # 计算手续费（简化：假设 0.1%）
        fee = executed_amount * self.FEE_RATE

        # 记录交易
        trade_data = {
            "account_name": account_name,
            "strategy_id": strategy_id,
            "symbol": symbol,
            "action": "BUY",
            "quantity": executed_qty,
            "price": current_price,
            "amount": executed_amount,
            "fee": fee,
            "trigger_reason": "strategy_auto",
            "executed_at": datetime.now(timezone.utc).isoformat()
        }

        trade_id = self.database.save_trade(trade_data)

        # 更新持仓
        self._update_position(account_name, symbol, executed_qty, current_price, "BUY")

        # 发送交易通知
        if account_webhook:
            # 获取更新后的余额
            new_balance = self.binance_client.get_account_balance()
            new_usdt_balance = new_balance.get("USDC", {}).get("free", 0)

            self.notifier.send_trade_notification(account_webhook, {
                "account_name": account_name,
                "strategy_id": strategy_id,
                "strategy_type": "N/A",  # 可以从配置获取
                "symbol": symbol,
                "action": "BUY",
                "quantity": executed_qty,
                "price": current_price,
                "amount": executed_amount,
                "fee": fee,
                "balance_before": usdt_balance,
                "balance_after": new_usdt_balance
            })

        logger.info(f"买入交易完成: {symbol} {executed_qty}股, ${executed_amount}")

        return {
            "success": True,
            "trade_id": trade_id,
            "order_id": order_id,
            "quantity": executed_qty,
            "amount": executed_amount,
            "adjusted_amount": required_amount if usdt_balance < signal.amount else None
        }

    def _execute_sell(
        self,
        account_name: str,
        strategy_id: str,
        signal: TradeSignal,
        symbol: str,
        account_webhook: str
    ) -> Dict[str, Any]:
        """执行卖出交易"""
        quantity = signal.quantity

        # 执行下单（带重试）
        order_result = self._place_order_with_retry(symbol, "SELL", quantity)

        # 解析订单结果
        executed_qty = float(order_result.get("executedQty", 0))
        executed_amount = float(order_result.get("cummulativeQuoteQty", 0))
        order_id = order_result.get("orderId")

        # 获取实时价格
        current_price = self.binance_client.get_realtime_price(symbol)

        # 计算手续费
        fee = executed_amount * self.FEE_RATE

        # 记录交易
        trade_data = {
            "account_name": account_name,
            "strategy_id": strategy_id,
            "symbol": symbol,
            "action": "SELL",
            "quantity": executed_qty,
            "price": current_price,
            "amount": executed_amount,
            "fee": fee,
            "trigger_reason": "strategy_auto" if strategy_id else "manual",
            "executed_at": datetime.now(timezone.utc).isoformat()
        }

        trade_id = self.database.save_trade(trade_data)

        # 更新持仓
        self._update_position(account_name, symbol, executed_qty, current_price, "SELL")

        # 发送交易通知
        if account_webhook:
            self.notifier.send_trade_notification(account_webhook, {
                "account_name": account_name,
                "strategy_id": strategy_id or "manual",
                "strategy_type": "N/A",
                "symbol": symbol,
                "action": "SELL",
                "quantity": executed_qty,
                "price": current_price,
                "amount": executed_amount,
                "fee": fee,
                "balance_before": 0,  # 简化
                "balance_after": 0
            })

        logger.info(f"卖出交易完成: {symbol} {executed_qty}股, ${executed_amount}")

        return {
            "success": True,
            "trade_id": trade_id,
            "order_id": order_id,
            "quantity": executed_qty,
            "amount": executed_amount
        }

    def _place_order_with_retry(self, symbol: str, side: str, quantity: float) -> Dict[str, Any]:
        """
        带重试的下单

        使用 retry_with_config 装饰器包装 Binance API 调用
        """
        @retry_with_config(self.retry_config)
        def place_order():
            return self.binance_client.place_order(symbol, side, quantity)

        return place_order()

    def _update_position(self, account_name: str, symbol: str, quantity: float, price: float, action: str):
        """
        更新持仓
        """
        # 防止数量为 0 时导致的除以零错误
        if quantity <= 0:
            logger.warning(f"持仓更新跳过: quantity={quantity} <= 0")
            return

        position = self.database.get_position(account_name, symbol)

        if action == "BUY":
            if position:
                # 更新平均成本
                old_qty = position["quantity"]
                old_cost = position["avg_cost"]
                new_qty = old_qty + quantity

                # 防止除以零
                if new_qty > 0:
                    new_cost = (old_qty * old_cost + quantity * price) / new_qty
                else:
                    logger.error(f"持仓更新异常: new_qty={new_qty} <= 0，跳过更新")
                    return

                self.database.update_position(account_name, symbol, {
                    "quantity": new_qty,
                    "avg_cost": new_cost
                })
            else:
                # 新建持仓
                self.database.update_position(account_name, symbol, {
                    "quantity": quantity,
                    "avg_cost": price
                })

        elif action == "SELL":
            if position:
                new_qty = position["quantity"] - quantity

                if new_qty > 0:
                    self.database.update_position(account_name, symbol, {
                        "quantity": new_qty,
                        "avg_cost": position["avg_cost"]  # 平均成本不变
                    })
                else:
                    # 清空持仓
                    self.database.update_position(account_name, symbol, {
                        "quantity": 0,
                        "avg_cost": 0
                    })
