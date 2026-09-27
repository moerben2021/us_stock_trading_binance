"""测试 yFinance 日期问题"""
import yfinance as yf
from datetime import datetime, timedelta

print("=" * 60)
print("测试 yFinance 日期处理")
print("=" * 60)

# 当前时间
now = datetime.now()
print(f"\n当前时间: {now}")
print(f"时间戳: {int(now.timestamp())}")

# 测试 1: 使用当前日期
print("\n测试 1: 使用当前日期作为结束时间")
print("-" * 60)
end_date = now
start_date = end_date - timedelta(days=30)
print(f"开始: {start_date}")
print(f"结束: {end_date}")

ticker = yf.Ticker("SPY")
try:
    data = ticker.history(start=start_date, end=end_date)
    print(f"[SUCCESS] 获取到 {len(data)} 条数据")
    if not data.empty:
        print(f"最新日期: {data.index[-1]}")
except Exception as e:
    print(f"[FAILED] {e}")

# 测试 2: 不指定结束日期（yFinance 自动处理）
print("\n测试 2: 不指定结束日期")
print("-" * 60)
start_date = now - timedelta(days=30)
print(f"开始: {start_date}")
print(f"结束: (自动)")

try:
    data = ticker.history(start=start_date)
    print(f"[SUCCESS] 获取到 {len(data)} 条数据")
    if not data.empty:
        print(f"最新日期: {data.index[-1]}")
        print(f"最后 5 天:")
        print(data.tail()[['Open', 'High', 'Low', 'Close', 'Volume']])
except Exception as e:
    print(f"[FAILED] {e}")

# 测试 3: 使用 period 参数
print("\n测试 3: 使用 period 参数")
print("-" * 60)
try:
    data = ticker.history(period="1mo")
    print(f"[SUCCESS] 获取到 {len(data)} 条数据")
    if not data.empty:
        print(f"最新日期: {data.index[-1]}")
        print(f"日期范围: {data.index[0]} 到 {data.index[-1]}")
except Exception as e:
    print(f"[FAILED] {e}")

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
