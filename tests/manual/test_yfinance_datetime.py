"""测试 yfinance 时间参数问题"""
import yfinance as yf
from datetime import datetime, timedelta
import os

# 设置代理
os.environ["HTTP_PROXY"] = "http://127.0.0.1:7990"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7990"
os.environ["http_proxy"] = "http://127.0.0.1:7990"
os.environ["https_proxy"] = "http://127.0.0.1:7990"

print("=" * 70)
print("测试 yfinance 时间参数问题")
print("=" * 70)

# 测试 1: 使用 datetime.now()（与 yfinance_client.py 相同）
print("\n测试 1: 使用 datetime.now()（yfinance_client.py 方式）")
print("-" * 70)

days = 30
end_date = datetime.now()
start_date = end_date - timedelta(days=days * 3)

print(f"start_date: {start_date}")
print(f"end_date: {end_date}")
print(f"start_date 类型: {type(start_date)}")
print(f"end_date 类型: {type(end_date)}")
print(f"start_date timezone: {start_date.tzinfo}")
print(f"end_date timezone: {end_date.tzinfo}")

ticker = yf.Ticker("SPY")

print("\n调用 ticker.history(start=start_date, end=end_date)...")
try:
    data = ticker.history(start=start_date, end=end_date)
    if data.empty:
        print("[FAILED] 返回空数据")
    else:
        print(f"[SUCCESS] 获取 {len(data)} 条数据")
        print(f"日期范围: {data.index[0]} 到 {data.index[-1]}")
except Exception as e:
    print(f"[FAILED] {e}")

# 测试 2: 使用日期字符串
print("\n\n测试 2: 使用日期字符串")
print("-" * 70)

start_str = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
end_str = datetime.now().strftime("%Y-%m-%d")

print(f"start_str: {start_str}")
print(f"end_str: {end_str}")

print("\n调用 ticker.history(start=start_str, end=end_str)...")
try:
    data = ticker.history(start=start_str, end=end_str)
    if data.empty:
        print("[FAILED] 返回空数据")
    else:
        print(f"[SUCCESS] 获取 {len(data)} 条数据")
        print(f"日期范围: {data.index[0]} 到 {data.index[-1]}")
except Exception as e:
    print(f"[FAILED] {e}")

# 测试 3: 只使用 start 参数，不指定 end
print("\n\n测试 3: 只使用 start 参数（不指定 end）")
print("-" * 70)

start_date3 = datetime.now() - timedelta(days=90)
print(f"start_date: {start_date3}")

print("\n调用 ticker.history(start=start_date3)...")
try:
    data = ticker.history(start=start_date3)
    if data.empty:
        print("[FAILED] 返回空数据")
    else:
        print(f"[SUCCESS] 获取 {len(data)} 条数据")
        print(f"日期范围: {data.index[0]} 到 {data.index[-1]}")
except Exception as e:
    print(f"[FAILED] {e}")

print("\n" + "=" * 70)
print("测试完成")
print("=" * 70)
