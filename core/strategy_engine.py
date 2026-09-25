"""策略引擎"""
import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from strategies.dca import DCAStrategy
from strategies.drawdown import DrawdownStrategy
from strategies.value_averaging import ValueAveragingStrategy
from integrations.wecom_notifier import WeComNotifier

logger = logging.getLogger(__name__)


class StrategyEngine:
    """
    策略引擎
    协调策略执行的完整流程：持仓同步 → 市场数据 → 策略计算 → 交易执行
    """

    def __init__(self, market_data_service, binance_client, database, trade_executor):
        """
        初始化策略引擎

        Args:
            market_data_service: 市场数据服务
            binance_client: Binance 客户端
            database: 数据库
            trade_executor: 交易执行器
        """
        self.market_data_service = market_data_service
        self.binance_client = binance_client
        self.database = database
        self.trade_executor = trade_executor

        # 注册所有策略
        self.strategies = {
            "dca": DCAStrategy(),
            "drawdown": DrawdownStrategy(),
            "value_averaging": ValueAveragingStrategy()
        }

        logger.info(f"策略引擎初始化完成，已注册策略: {list(self.strategies.keys())}")

    def execute_strategy(
        self,
        account_config: Dict[str, Any],
        strategy_instance: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行策略

        Args:
            account_config: 账户配置
            strategy_instance: 策略实例配置

        Returns:
            执行结果字典
        """
        account_name = account_config.get("name")
        strategy_id = strategy_instance.get("id")
        strategy_type = strategy_instance.get("type")
        symbol = strategy_instance.get("symbol")
        strategy_config = strategy_instance.get("config", {})
        webhook_url = account_config.get("webhook_url")

        logger.info(f"开始执行策略: {strategy_id} ({strategy_type}) - {account_name}/{symbol}")

        try:
            # 1. 同步持仓
            self._sync_position(account_name, symbol, webhook_url)

            # 2. 获取策略实例
            strategy = self.strategies.get(strategy_type)
            if not strategy:
                raise ValueError(f"未知的策略类型: {strategy_type}")

            # 3. 获取数据需求
            data_requirement = strategy.get_required_data(strategy_config)

            # 4. 获取市场数据
            market_data = self.market_data_service.get_market_data(
                symbol=symbol,
                days_required=data_requirement.history_days
            )

            # 5. 获取当前持仓（同步后的）
            position = self.database.get_position(account_name, symbol)

            # 6. 计算交易信号
            signal = strategy.calculate(
                account_config=account_config,
                strategy_config=strategy_config,
                market_data=market_data,
                position=position
            )

            logger.info(f"策略信号: {signal.action}, 金额: {signal.amount}, 原因: {signal.reason}")

            # 7. 执行交易（如果不是 HOLD）
            trade_result = None
            trade_id = None

            if signal.action != "HOLD":
                trade_result = self.trade_executor.execute_trade(
                    account_name=account_name,
                    strategy_id=strategy_id,
                    signal=signal,
                    symbol=symbol,
                    account_webhook=webhook_url
                )

                if trade_result.get("success"):
                    trade_id = trade_result.get("trade_id")
                    logger.info(f"交易执行成功: trade_id={trade_id}")
                else:
                    logger.warning(f"交易执行失败: {trade_result.get('error')}")

            # 8. 构建执行记录
            calculation_result = self._build_calculation_result(
                strategy_config, market_data, signal, position
            )
            market_data_snapshot = self._build_market_data_snapshot(market_data)

            execution_data = {
                "strategy_id": strategy_id,
                "account_name": account_name,
                "executed_at": datetime.now(timezone.utc).isoformat(),
                "signal": signal.action,
                "signal_amount": signal.amount,
                "status": "success" if (signal.action == "HOLD" or (trade_result and trade_result.get("success"))) else "failed",
                "error_message": None if signal.action == "HOLD" else trade_result.get("error") if trade_result else None,
                "trade_id": trade_id,
                "market_data_snapshot": market_data_snapshot,
                "calculation_result": calculation_result
            }

            # 9. 保存执行记录
            execution_id = self.database.save_strategy_execution(execution_data)

            logger.info(f"策略执行完成: execution_id={execution_id}")

            return {
                "success": True,
                "execution_id": execution_id,
                "signal": signal.action,
                "signal_amount": signal.amount,
                "trade_id": trade_id
            }

        except Exception as e:
            logger.error(f"策略执行异常: {e}", exc_info=True)

            # 保存失败的执行记录
            try:
                execution_data = {
                    "strategy_id": strategy_id,
                    "account_name": account_name,
                    "executed_at": datetime.now(timezone.utc).isoformat(),
                    "signal": "HOLD",
                    "signal_amount": 0,
                    "status": "failed",
                    "error_message": str(e),
                    "trade_id": None,
                    "market_data_snapshot": "{}",
                    "calculation_result": "{}"
                }
                self.database.save_strategy_execution(execution_data)
            except Exception as save_error:
                logger.error(f"保存失败记录时出错: {save_error}", exc_info=True)

            return {
                "success": False,
                "error": str(e)
            }

    def _sync_position(self, account_name: str, symbol: str, webhook_url: Optional[str] = None):
        """
        同步持仓（Binance API vs 本地数据库）

        Args:
            account_name: 账户名称
            symbol: 标的代码
            webhook_url: 企业微信 Webhook URL（可选）
        """
        try:
            # 获取 Binance 持仓（权威源）
            binance_position = self.binance_client.get_position(symbol)
            binance_qty = binance_position.get("quantity", 0)

            # 获取本地持仓
            local_position = self.database.get_position(account_name, symbol)
            local_qty = local_position.get("quantity", 0) if local_position else 0

            # 比较持仓（容忍度 0.01）
            qty_diff = abs(binance_qty - local_qty)

            if qty_diff > 0.01:
                logger.warning(
                    f"持仓不匹配: {symbol}, "
                    f"Binance={binance_qty}, 本地={local_qty}, "
                    f"差异={qty_diff}"
                )

                # 更新本地持仓为 Binance 的值
                avg_cost = local_position.get("avg_cost", 0) if local_position else 0
                self.database.update_position(account_name, symbol, {
                    "quantity": binance_qty,
                    "avg_cost": avg_cost
                })

                logger.info(f"已更新本地持仓: {symbol} → {binance_qty}")

                # 发送告警通知
                if webhook_url:
                    try:
                        notifier = WeComNotifier()
                        notifier.send_alert_notification(webhook_url, {
                            "alert_type": "position_mismatch",
                            "message": "持仓不匹配，已同步",
                            "details": f"{symbol}: Binance={binance_qty}, 本地={local_qty}, 已更新为 {binance_qty}"
                        })
                    except Exception as notify_error:
                        logger.error(f"发送持仓不匹配告警失败: {notify_error}", exc_info=True)
            else:
                logger.debug(f"持仓一致: {symbol} = {binance_qty}")

        except Exception as e:
            logger.error(f"持仓同步失败: {e}", exc_info=True)
            # 持仓同步失败不应中断策略执行，继续执行

    def _build_calculation_result(
        self,
        strategy_config: Dict[str, Any],
        market_data: Dict[str, Any],
        signal: Any,
        position: Optional[Dict[str, Any]]
    ) -> str:
        """
        构建计算结果快照（JSON）

        Args:
            strategy_config: 策略配置
            market_data: 市场数据
            signal: 交易信号
            position: 持仓

        Returns:
            JSON 字符串
        """
        result = {
            "config": strategy_config,
            "position": {
                "quantity": position.get("quantity", 0) if position else 0,
                "avg_cost": position.get("avg_cost", 0) if position else 0
            },
            "market_data": {
                "current_price": market_data.get("current_price", 0),
                "highest_price": market_data.get("highest_price", 0),
                "lowest_price": market_data.get("lowest_price", 0)
            },
            "signal": {
                "action": signal.action,
                "amount": signal.amount,
                "quantity": signal.quantity if hasattr(signal, "quantity") and signal.quantity else 0,
                "reason": signal.reason
            }
        }

        return json.dumps(result, ensure_ascii=False)

    def _build_market_data_snapshot(self, market_data: Dict[str, Any]) -> str:
        """
        构建市场数据快照（JSON，排除 DataFrame）

        Args:
            market_data: 市场数据

        Returns:
            JSON 字符串
        """
        snapshot = {
            "current_price": market_data.get("current_price", 0),
            "highest_price": market_data.get("highest_price", 0),
            "lowest_price": market_data.get("lowest_price", 0),
            "has_history": not market_data.get("history_data").empty if market_data.get("history_data") is not None else False
        }

        return json.dumps(snapshot, ensure_ascii=False)
