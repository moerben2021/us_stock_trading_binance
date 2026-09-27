"""测试 yFinance Ticker 参数"""
import yfinance as yf
import inspect

print("=" * 70)
print("yFinance Ticker 参数检查")
print("=" * 70)

print(f"\nyFinance 版本: {yf.__version__}")

# 查看 Ticker.__init__ 的参数
print("\n[Ticker.__init__ 参数]")
print("-" * 70)
sig = inspect.signature(yf.Ticker.__init__)
print(f"参数列表: {list(sig.parameters.keys())}")

# 查看完整文档
print("\n[Ticker.__init__ 文档]")
print("-" * 70)
print(yf.Ticker.__init__.__doc__)

# 查看 history 方法的参数
print("\n[Ticker.history 参数]")
print("-" * 70)
sig = inspect.signature(yf.Ticker.history)
print(f"参数列表: {list(sig.parameters.keys())}")

print("\n" + "=" * 70)
