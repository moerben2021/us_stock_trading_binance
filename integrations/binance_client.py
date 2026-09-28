"""Binance API 客户端"""
import hmac
import hashlib
import time
import requests
import logging
from typing import Dict, Any, Optional
from urllib.parse import urlencode
from utils.rate_limiter import RateLimiter
from utils.retry import retry_with_config, RetryConfig

logger = logging.getLogger(__name__)

class BinanceClient:
    """Binance 美股交易客户端"""

    # Binance 全球站 API 端点
    BASE_URL = "https://api.binance.com"

    # 美股 API 端点常量
    ENDPOINT_QUOTE = "/sapi/v1/equity/market/quote"  # 获取报价
    ENDPOINT_EXCHANGE_INFO = "/sapi/v1/equity/market/exchangeInfo"  # 交易所信息
    ENDPOINT_ORDER = "/sapi/v1/equity/order/place"  # 下单
    ENDPOINT_ORDER_DETAIL = "/sapi/v1/equity/order/detail"  # 订单详情

    # 资金账户 API 端点
    ENDPOINT_FUNDING_ASSET = "/sapi/v1/asset/get-funding-asset"  # 资金账户（股票交易专用）

    def __init__(self, api_key: str, secret_key: str, proxies: Optional[Dict[str, str]] = None):
        """
        初始化客户端

        Args:
            api_key: API Key
            secret_key: Secret Key
            proxies: 代理配置，格式如 {"http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890"}
        """
        self.api_key = api_key
        self.secret_key = secret_key
        self.proxies = proxies

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
        获取实时价格（美股）

        Args:
            symbol: 股票代码（如 SPY, QQQ, AAPL）

        Returns:
            实时价格（使用中间价：(bid + ask) / 2）
        """
        params = {"symbol": symbol}

        response = self._call_api("GET", self.ENDPOINT_QUOTE, params)

        # 美股 API 返回 bidPrice 和 askPrice
        bid_price = float(response["bidPrice"])
        ask_price = float(response["askPrice"])

        # 使用中间价
        price = (bid_price + ask_price) / 2

        logger.info(f"获取 {symbol} 实时价格: ${price:.2f} (bid: ${bid_price:.2f}, ask: ${ask_price:.2f})")
        return price

    def get_account_balance(self) -> Dict[str, Dict[str, float]]:
        """
        获取资金账户余额（包含股票持仓和 USDC 现金）

        使用 /sapi/v1/asset/get-funding-asset 端点查询资金账户中的所有资产。
        资金账户是股票交易专用账户，与现货账户独立。

        Returns:
            余额字典，格式：{"USDC": {"free": 312.24, "locked": 49.77}, "SPY": {"free": 10.5, "locked": 0.0}}
        """
        try:
            # 调用资金账户 API（使用 POST 方法）
            response = self._call_api("POST", self.ENDPOINT_FUNDING_ASSET, {}, signed=True)

            balances = {}

            # 响应格式：[{"asset": "USDC", "free": "312.24", "locked": "49.77", ...}, ...]
            for item in response:
                asset = item.get("asset")
                free = float(item.get("free", 0))
                locked = float(item.get("locked", 0))

                # 只返回有余额的资产
                if free > 0 or locked > 0:
                    balances[asset] = {
                        "free": free,
                        "locked": locked
                    }

            logger.info(f"获取资金账户余额: {len(balances)} 个资产")
            return balances

        except Exception as e:
            logger.error(f"获取资金账户余额失败: {e}", exc_info=True)
            raise

    def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取持仓信息（从资金账户查询）

        使用 /sapi/v1/asset/getUserAsset 端点查询特定股票的持仓。

        Args:
            symbol: 股票代码

        Returns:
            持仓信息，包含数量和平均成本；如果无持仓返回 None
        """
        try:
            # 从账户余额中查找该股票
            balance = self.get_account_balance()

            if symbol in balance:
                free = balance[symbol]["free"]
                locked = balance[symbol]["locked"]
                quantity = free + locked

                if quantity > 0:
                    logger.info(f"获取 {symbol} 持仓: {quantity} 股")
                    return {
                        "symbol": symbol,
                        "quantity": quantity,
                        "avg_cost": 0.0  # TODO: 需要从交易历史计算平均成本
                    }

            logger.info(f"获取 {symbol} 持仓: 无持仓")
            return None

        except Exception as e:
            logger.error(f"获取 {symbol} 持仓失败: {e}", exc_info=True)
            return None

    def place_order(self, symbol: str, side: str, quantity: float) -> Dict[str, Any]:
        """
        下市价单（美股）

        Args:
            symbol: 股票代码（如 SPY, QQQ）
            side: BUY 或 SELL
            quantity: 对于市价买单，这是金额（notional）；对于市价卖单，这是数量（quantity）

        Returns:
            订单信息

        Raises:
            ValueError: 如果 quantity <= 0
        """
        if quantity <= 0:
            raise ValueError(f"订单金额/数量必须大于 0，当前值为 {quantity}")

        # 构造参数
        params = {
            "symbol": symbol,
            "side": side,
            "orderType": "MARKET",  # 使用 orderType 而不是 type
            "tokenize": "false",  # 不进行代币化，持有原生美股
        }

        # 市价买单使用 notional（金额），市价卖单使用 quantity（数量）
        if side == "BUY":
            params["notional"] = quantity  # 买入：传入金额（如 $6）
        else:
            params["quantity"] = quantity  # 卖出：传入股数

        response = self._call_api("POST", self.ENDPOINT_ORDER, params, signed=True)

        # 仅记录关键字段，避免敏感信息泄露
        order_id = response.get("orderId") or response.get("id")
        status = response.get("status")
        logger.debug(f"订单响应: orderId={order_id}, status={status}, symbol={symbol}, side={side}")
        logger.info(f"下单成功: {side} {symbol}, 订单ID: {order_id}")
        return response

    def get_order_detail(self, order_id: str) -> Dict[str, Any]:
        """
        查询订单详情

        Args:
            order_id: 订单ID

        Returns:
            订单详情，包含成交信息
        """
        try:
            params = {"orderId": order_id}
            response = self._call_api("GET", self.ENDPOINT_ORDER_DETAIL, params, signed=True)

            logger.info(f"订单详情查询成功: orderId={order_id}")
            logger.debug(f"订单详情: {response}")

            return response

        except Exception as e:
            logger.error(f"查询订单详情失败: {e}", exc_info=True)
            raise

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
                response = requests.get(url, headers=headers, params=params, proxies=self.proxies, timeout=10)
            elif method == "POST":
                response = requests.post(url, headers=headers, params=params, proxies=self.proxies, timeout=10)
            else:
                raise ValueError(f"不支持的 HTTP 方法: {method}")

            # 处理限流响应
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 60))
                logger.warning(f"触发 API 限流，等待 {retry_after} 秒")
                time.sleep(retry_after)
                # 重新调用（由装饰器处理）
                raise Exception("API 限流，重试中...")

            # 在 raise_for_status 之前记录详细错误信息
            if response.status_code >= 400:
                try:
                    error_detail = response.json()
                    error_code = error_detail.get('code', 'N/A')
                    error_msg = error_detail.get('msg', 'N/A')
                    logger.error(f"API 错误响应: code={error_code}, msg={error_msg}")
                except:
                    logger.error(f"API 错误响应（非 JSON）: status={response.status_code}, body_prefix={response.text[:100]}")

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

        注意：使用 urlencode 对参数进行 URL 编码后再签名
        """
        # 使用 urlencode 生成 query string（会自动进行 URL 编码）
        query_string = urlencode(params)

        signature = hmac.new(
            self.secret_key.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        return signature
