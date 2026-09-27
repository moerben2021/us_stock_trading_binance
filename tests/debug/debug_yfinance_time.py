"""调试 yfinance 时间参数传递"""
import yfinance as yf
from datetime import datetime, timedelta
import os
import logging

# 设置代理
os.environ["HTTP_PROXY"] = "http://127.0.0.1:7990"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7990"
os.environ["http_proxy"] = "http://127.0.0.1:7990"
os.environ["https_proxy"] = "http://127.0.0.1:7990"

# 启用 yfinance 的调试日志
logging.basicConfig(level=logging.DEBUG)
yf_logger = logging.getLogger('yfinance')
yf_logger.setLevel(logging.DEBUG)

print("=" * 70)
print("调试 yfinance 时间参数传递")
print("=" * 70)

# 完全复制 yfinance_client.py 的逻辑
days = 30
end_date = datetime.now()
start_date = end_date - timedelta(days=days * 3)

print(f"\n传入参数:")
print(f"  start_date: {start_date}")
print(f"  end_date: {end_date}")
print(f"  类型: {type(start_date)}, {type(end_date)}")
print(f"  时区: {start_date.tzinfo}, {end_date.tzinfo}")

ticker = yf.Ticker("SPY")

print(f"\n调用 ticker.history(start={start_date}, end={end_date})...")
print("-" * 70)

try:
    data = ticker.history(start=start_date, end=end_date)

    print(f"\n结果:")
    if data.empty:
        print("  [FAILED] 返回空数据")
    else:
        print(f"  [SUCCESS] 获取 {len(data)} 条数据")
        print(f"  日期范围: {data.index[0]} 到 {data.index[-1]}")
except Exception as e:
    print(f"\n  [FAILED] 异常: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
