"""日期工具函数"""
from datetime import datetime, timedelta
import pytz
import pandas_market_calendars as mcal

# 获取美股交易日历
NYSE = mcal.get_calendar('NYSE')

def is_trading_day(date: datetime) -> bool:
    """
    判断是否为美股交易日

    Args:
        date: 日期

    Returns:
        是否为交易日
    """
    # 转换为美东时间
    eastern = pytz.timezone('America/New_York')
    if date.tzinfo is None:
        date = eastern.localize(date)
    else:
        date = date.astimezone(eastern)

    # 获取该日期的交易日信息
    schedule = NYSE.schedule(start_date=date.date(), end_date=date.date())
    return len(schedule) > 0

def get_next_trading_day(date: datetime) -> datetime:
    """
    获取下一个交易日

    Args:
        date: 起始日期

    Returns:
        下一个交易日
    """
    eastern = pytz.timezone('America/New_York')
    if date.tzinfo is None:
        date = eastern.localize(date)
    else:
        date = date.astimezone(eastern)

    # 从明天开始查找
    next_date = date + timedelta(days=1)

    # 获取未来30天的交易日
    schedule = NYSE.schedule(
        start_date=next_date.date(),
        end_date=(next_date + timedelta(days=30)).date()
    )

    if len(schedule) > 0:
        trading_day = schedule.index[0]
        return eastern.localize(datetime.combine(trading_day.date(), datetime.min.time()))

    # 如果30天内没有交易日，返回明天（异常情况）
    return next_date

def get_us_trading_day() -> str:
    """
    获取美东时间当前的交易日（YYYY-MM-DD格式）

    Returns:
        交易日字符串
    """
    eastern = pytz.timezone('America/New_York')
    now = datetime.now(eastern)

    if is_trading_day(now):
        return now.strftime('%Y-%m-%d')
    else:
        # 如果今天不是交易日，返回最近的交易日
        # 获取过去7天的交易日
        schedule = NYSE.schedule(
            start_date=(now - timedelta(days=7)).date(),
            end_date=now.date()
        )

        if len(schedule) > 0:
            trading_day = schedule.index[-1]
            return trading_day.strftime('%Y-%m-%d')

        # 异常情况，返回今天
        return now.strftime('%Y-%m-%d')
