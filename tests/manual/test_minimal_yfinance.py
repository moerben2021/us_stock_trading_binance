"""最小化测试：验证环境变量设置时机"""
import sys
import os
from pathlib import Path

print("=" * 70)
print("步骤 1: 设置环境变量（在任何 import 之前）")
print("=" * 70)

sys.path.insert(0, str(Path(__file__).parent))

# 设置环境变量
os.environ["HTTP_PROXY"] = "http://127.0.0.1:7990"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7990"
os.environ["http_proxy"] = "http://127.0.0.1:7990"
os.environ["https_proxy"] = "http://127.0.0.1:7990"

print(f"HTTP_PROXY = {os.environ.get('HTTP_PROXY')}")
print(f"HTTPS_PROXY = {os.environ.get('HTTPS_PROXY')}")

print("\n" + "=" * 70)
print("步骤 2: 导入 yfinance（环境变量已设置）")
print("=" * 70)

import yfinance as yf

print(f"yFinance 版本: {yf.__version__}")

print("\n" + "=" * 70)
print("步骤 3: 测试获取数据")
print("=" * 70)

ticker = yf.Ticker("SPY")

print("\n测试 1: 使用 period 参数")
try:
    data = ticker.history(period="5d")
    if data.empty:
        print("[FAILED] 返回空数据")
    else:
        print(f"[SUCCESS] 获取 {len(data)} 条数据")
        print(f"日期范围: {data.index[0]} 到 {data.index[-1]}")
except Exception as e:
    print(f"[FAILED] {e}")

print("\n测试 2: 使用 start/end 参数")
from datetime import datetime, timedelta
try:
    end_date = datetime.now()
    start_date = end_date - timedelta(days=5)
    data = ticker.history(start=start_date, end=end_date)
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
