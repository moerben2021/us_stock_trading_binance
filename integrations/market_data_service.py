"""市场数据服务（带缓存）"""
import time
import logging
from typing import Dict, Any, Optional
import pandas as pd
from utils.date_utils import get_us_trading_day

logger = logging.getLogger(__name__)

class MarketDataService:
    """
    市场数据服务
    提供历史数据和实时价格，带缓存优化
    """

    def __init__(self, yfinance_client, binance_client):
        """
        初始化市场数据服务

        Args:
            yfinance_client: yFinance 客户端
            binance_client: Binance 客户端
        """
        self.yfinance_client = yfinance_client
        self.binance_client = binance_client

        # 历史数据缓存：{(symbol, days, trading_day): (data, timestamp)}
        self.history_cache = {}

        # 实时价格缓存：{symbol: (price, timestamp)}
        self.realtime_cache = {}

        # 当前交易日
        self.current_trading_day = get_us_trading_day()

        # 缓存配置
        self.realtime_ttl = 60  # 实时价格缓存 1 分钟

    def get_market_data(self, symbol: str, days_required: int) -> Dict[str, Any]:
        """
        获取市场数据（历史 + 实时）

        Args:
            symbol: 股票代码
            days_required: 需要的历史天数

        Returns:
            市场数据字典，包含：
            - history_data: DataFrame 历史数据
            - current_price: float 当前价格
            - highest_price: float 历史最高价
            - lowest_price: float 历史最低价
        """
        # 检查是否需要清空缓存（新交易日）
        today = get_us_trading_day()
        if self.current_trading_day != today:
            logger.info(f"新交易日 {today}，清空历史数据缓存")
            self.history_cache.clear()
            self.current_trading_day = today

        # 缓存 key（使用 self.current_trading_day 确保与清空逻辑一致）
        cache_key = (symbol, days_required, self.current_trading_day)

        # 检查缓存
        if cache_key in self.history_cache:
            logger.debug(f"使用缓存的历史数据: {symbol}")
            cached_data, _ = self.history_cache[cache_key]
            history_data = cached_data
        else:
            # 从 yFinance 获取
            logger.info(f"从 yFinance 获取 {symbol} 的历史数据")
            history_data = self.yfinance_client.get_history_data(symbol, days_required)

            # 缓存
            self.history_cache[cache_key] = (history_data, time.time())

        # 获取实时价格
        current_price = self.get_realtime_price(symbol)

        # 计算统计数据
        if not history_data.empty:
            highest_price = history_data['High'].max()
            lowest_price = history_data['Low'].min()
        else:
            highest_price = current_price
            lowest_price = current_price

        return {
            "history_data": history_data,
            "current_price": current_price,
            "highest_price": highest_price,
            "lowest_price": lowest_price
        }

    def get_realtime_price(self, symbol: str) -> float:
        """
        获取实时价格（带缓存）

        Args:
            symbol: 股票代码

        Returns:
            实时价格
        """
        now = time.time()

        # 检查缓存
        if symbol in self.realtime_cache:
            price, timestamp = self.realtime_cache[symbol]
            if now - timestamp < self.realtime_ttl:
                logger.debug(f"使用缓存的实时价格: {symbol} = ${price}")
                return price

        # 从 Binance 获取
        logger.info(f"从 Binance 获取 {symbol} 的实时价格")
        price = self.binance_client.get_realtime_price(symbol)

        # 缓存
        self.realtime_cache[symbol] = (price, now)

        return price
