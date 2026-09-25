"""Binance API 客户端"""
import hmac
import hashlib
import time
import requests
import logging
from typing import Dict, Any, Optional
from utils.rate_limiter import RateLimiter
from utils.retry import retry_with_config, RetryConfig

logger = logging.getLogger(__name__)

class BinanceClient:
    """Binance 美股交易客户端"""

    # 注意：这里使用 Binance 美股 API 的实际端点
    # 如果找不到官方文档，这部分需要根据实际 API 调整
    BASE_URL = "https://api.binance.us"  # 美股可能是 binance.us

    # API 端点常量
    ENDPOINT_TICKER_PRICE = "/api/v3/ticker/price"
    ENDPOINT_ACCOUNT = "/api/v3/account"
    ENDPOINT_ORDER = "/api/v3/order"

    def __init__(self, api_key: str, secret_key: str):
        """
        初始化客户端

        Args:
            api_key: API Key
            secret_key: Secret Key
        """
        self.api_key = api_key
        self.secret_key = secret_key

        # 初始化限流器
        self.rate_limiter = RateLimiter(
            max_requests_per_minute=1200,
            max_requests_per_second=20
        )

        # 重试配置
        self.retry_config = RetryConfig(
            max_attempts=3,
            interval_seconds=5,
            backoff="exponential"
        )

    def get_realtime_price(self, symbol: str) -> float:
        """
        获取实时价格

        Args:
            symbol: 股票代码

        Returns:
            实时价格
        """
        params = {"symbol": symbol}

        response = self._call_api("GET", self.ENDPOINT_TICKER_PRICE, params)
        price = float(response["price"])

        logger.info(f"获取 {symbol} 实时价格: ${price}")
        return price

    def get_account_balance(self) -> Dict[str, Dict[str, float]]:
        """
        获取账户余额

        Returns:
            余额字典，格式：{"USDT": {"free": 10000.0, "locked": 0.0}}
        """
        response = self._call_api("GET", self.ENDPOINT_ACCOUNT, {}, signed=True)

        balances = {}
        for item in response.get("balances", []):
            asset = item["asset"]
            balances[asset] = {
                "free": float(item["free"]),
                "locked": float(item["locked"])
            }

        logger.info(f"获取账户余额: {len(balances)} 个资产")
        return balances

    def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取持仓信息

        Args:
            symbol: 股票代码

        Returns:
            持仓信息，包含数量和平均成本
        """
        # 注意：这个方法需要根据 Binance 美股 API 的实际实现调整
        # 可能需要通过账户信息和历史交易来计算
        response = self._call_api("GET", self.ENDPOINT_ACCOUNT, {}, signed=True)

        # 简化实现：从余额中查找
        for item in response.get("balances", []):
            if item["asset"] == symbol:
                quantity = float(item["free"]) + float(item["locked"])
                if quantity > 0:
                    # 实际应该从交易历史计算平均成本
                    return {
                        "symbol": symbol,
                        "quantity": quantity,
                        "avg_cost": 0.0  # 需要从交易历史计算
                    }

        return None

    def place_order(self, symbol: str, side: str, quantity: float) -> Dict[str, Any]:
        """
        下市价单

        Args:
            symbol: 股票代码
            side: BUY 或 SELL
            quantity: 数量（必须大于 0）

        Returns:
            订单信息

        Raises:
            ValueError: 如果 quantity <= 0
        """
        if quantity <= 0:
            raise ValueError(f"订单数量必须大于 0，当前值为 {quantity}")

        params = {
            "symbol": symbol,
            "side": side,
            "type": "MARKET",
            "quantity": quantity
        }

        response = self._call_api("POST", self.ENDPOINT_ORDER, params, signed=True)

        logger.info(f"下单成功: {side} {quantity} {symbol}, 订单ID: {response['orderId']}")
        return response

    @retry_with_config(RetryConfig(max_attempts=3, interval_seconds=5, backoff="exponential"))
    def _call_api(self, method: str, endpoint: str, params: Dict[str, Any], signed: bool = False) -> Dict[str, Any]:
        """
        调用 API

        Args:
            method: HTTP 方法
            endpoint: API 端点
            params: 参数
            signed: 是否需要签名

        Returns:
            API 响应
        """
        # 等待限流器许可
        self.rate_limiter.acquire()

        url = self.BASE_URL + endpoint
        headers = {
            "X-MBX-APIKEY": self.api_key
        }

        # 添加时间戳（签名请求需要）
        if signed:
            params["timestamp"] = int(time.time() * 1000)
            # 生成签名（不包含 signature 自身）
            signature = self._generate_signature(params)
            # 将签名添加到参数中
            params["signature"] = signature

        try:
            if method == "GET":
                response = requests.get(url, headers=headers, params=params, timeout=10)
            elif method == "POST":
                response = requests.post(url, headers=headers, params=params, timeout=10)
            else:
                raise ValueError(f"不支持的 HTTP 方法: {method}")

            # 处理限流响应
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 60))
                logger.warning(f"触发 API 限流，等待 {retry_after} 秒")
                time.sleep(retry_after)
                # 重新调用（由装饰器处理）
                raise Exception("API 限流，重试中...")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"API 调用失败: {e}")
            raise

    def _generate_signature(self, params: Dict[str, Any]) -> str:
        """
        生成请求签名

        Args:
            params: 请求参数

        Returns:
            签名字符串
        """
        query_string = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
        signature = hmac.new(
            self.secret_key.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        return signature
