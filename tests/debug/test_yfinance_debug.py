"""诊断 yFinance 问题"""
import sys
import yfinance as yf
from datetime import datetime, timedelta
import logging

# 配置日志显示 yFinance 内部信息
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

print("=" * 60)
print("yFinance 诊断信息")
print("=" * 60)

# 版本信息
print(f"\nPython 版本: {sys.version}")
print(f"yFinance 版本: {yf.__version__}")

# 测试与代码一致的调用方式
print("\n" + "=" * 60)
print("测试代码中的实际调用方式")
print("=" * 60)

symbol = "SPY"
days = 30

# 完全复制 yfinance_client.py 的逻辑
end_date = datetime.now()
start_date = end_date - timedelta(days=days * 3)

print(f"\n参数:")
print(f"  symbol: {symbol}")
print(f"  days: {days}")
print(f"  start_date: {start_date}")
print(f"  end_date: {end_date}")
print(f"  start_date 类型: {type(start_date)}")
print(f"  end_date 类型: {type(end_date)}")

print("\n开始调用 ticker.history()...")
ticker = yf.Ticker(symbol)

try:
    data = ticker.history(start=start_date, end=end_date)

    if data.empty:
        print(f"[WARNING] 返回数据为空")
    else:
        print(f"[SUCCESS] 获取到 {len(data)} 条数据")
        print(f"\n数据范围:")
        print(f"  最早: {data.index[0]}")
        print(f"  最新: {data.index[-1]}")
        print(f"\n最后 3 天数据:")
        print(data.tail(3)[['Open', 'High', 'Low', 'Close', 'Volume']])

except Exception as e:
    print(f"[ERROR] 异常: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("诊断完成")
print("=" * 60)
