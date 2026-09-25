"""yFinance 数据获取客户端"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import logging
from utils.date_utils import is_trading_day as utils_is_trading_day

logger = logging.getLogger(__name__)


class YFinanceClient:
    """yFinance 客户端，用于获取历史行情数据"""

    def get_history_data(self, symbol: str, days: int) -> pd.DataFrame:
        """
        获取历史日行情数据

        Args:
            symbol: 股票代码
            days: 需要的天数

        Returns:
            包含历史数据的 DataFrame
            列：Date, Open, High, Low, Close, Adj Close, Volume
        """
        try:
            # 计算起始日期（多取一些天数以确保有足够的交易日数据）
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days * 2)

            # 下载数据
            ticker = yf.Ticker(symbol)
            data = ticker.history(start=start_date, end=end_date)

            if data.empty:
                logger.warning(f"未获取到 {symbol} 的历史数据")
                return pd.DataFrame()

            # 只保留最近 N 个交易日的数据
            if len(data) > days:
                data = data.tail(days)

            logger.info(f"成功获取 {symbol} 最近 {len(data)} 天的历史数据")
            return data

        except Exception as e:
            logger.error(f"获取 {symbol} 历史数据失败: {e}")
            raise

    def is_trading_day(self, date: datetime) -> bool:
        """
        判断是否为美股交易日

        Args:
            date: 日期

        Returns:
            是否为交易日
        """
        return utils_is_trading_day(date)
