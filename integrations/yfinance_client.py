"""yFinance 数据获取客户端"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import logging
from utils.date_utils import is_trading_day as utils_is_trading_day

logger = logging.getLogger(__name__)


class YFinanceClient:
    """yFinance 客户端，用于获取历史行情数据"""

    def __init__(self):
        """
        初始化 yFinance 客户端

        注意：yFinance 会自动使用环境变量中的代理配置（HTTP_PROXY/HTTPS_PROXY）
        """
        logger.info("yFinance 客户端初始化完成（使用环境变量代理配置）")

    def get_history_data(self, symbol: str, days: int) -> pd.DataFrame:
        """
        获取历史日行情数据（带重试）

        Args:
            symbol: 股票代码
            days: 需要的天数

        Returns:
            包含历史数据的 DataFrame
            列：Date, Open, High, Low, Close, Adj Close, Volume
        """
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                # 创建 Ticker 对象（不传 session，让 yFinance 自动处理代理）
                ticker = yf.Ticker(symbol)

                # 优先使用 period 参数（更稳定，避免时间戳问题）
                if days <= 5:
                    period = "5d"
                elif days <= 30:
                    period = "1mo"
                elif days <= 90:
                    period = "3mo"
                else:
                    period = "1y"

                logger.info(f"获取 {symbol} 历史数据，period={period}")
                data = ticker.history(period=period)

                if data.empty:
                    retry_count += 1
                    if retry_count < max_retries:
                        logger.warning(f"未获取到 {symbol} 的历史数据，重试 {retry_count}/{max_retries}")
                        continue
                    else:
                        logger.warning(f"未获取到 {symbol} 的历史数据（已重试 {max_retries} 次）")
                        return pd.DataFrame()

                # 只保留最近 N 个交易日的数据
                if len(data) > days:
                    data = data.tail(days)

                logger.info(f"成功获取 {symbol} 最近 {len(data)} 天的历史数据")
                return data

            except Exception as e:
                retry_count += 1
                if retry_count < max_retries:
                    logger.warning(f"获取 {symbol} 历史数据失败: {e}，重试 {retry_count}/{max_retries}")
                else:
                    logger.error(f"获取 {symbol} 历史数据失败（已重试 {max_retries} 次）: {e}")
                    # 不抛出异常，返回空 DataFrame，让策略处理
                    return pd.DataFrame()

        return pd.DataFrame()

    def is_trading_day(self, date: datetime) -> bool:
        """
        判断是否为美股交易日

        Args:
            date: 日期

        Returns:
            是否为交易日
        """
        return utils_is_trading_day(date)
