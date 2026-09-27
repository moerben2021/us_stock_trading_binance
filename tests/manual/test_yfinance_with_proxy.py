"""测试 yFinance 使用代理"""
import yaml
from integrations.yfinance_client import YFinanceClient

print("=" * 70)
print("测试 yFinance 使用代理")
print("=" * 70)

# 1. 加载代理配置
print("\n[步骤 1] 加载代理配置")
print("-" * 70)
with open("system.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

proxy_config = config.get("system", {}).get("proxy", {})
proxy_enabled = proxy_config.get("enabled", False)

if proxy_enabled:
    proxies = {
        "http": proxy_config.get("http"),
        "https": proxy_config.get("https")
    }
    print(f"代理配置: {proxies}")
else:
    proxies = None
    print("代理未启用")

# 2. 创建 yFinance 客户端（传入代理）
print("\n[步骤 2] 创建 yFinance 客户端")
print("-" * 70)
client = YFinanceClient(proxies=proxies)

# 3. 测试获取历史数据
print("\n[步骤 3] 测试获取历史数据")
print("-" * 70)

symbols = ["SPY", "QQQ"]
days = 30

for symbol in symbols:
    print(f"\n测试 {symbol}:")
    try:
        data = client.get_history_data(symbol, days)

        if data.empty:
            print(f"  [WARNING] 返回空数据")
        else:
            print(f"  [SUCCESS] 获取 {len(data)} 条数据")
            print(f"  日期范围: {data.index[0]} 到 {data.index[-1]}")
            print(f"  最新收盘价: ${data.iloc[-1]['Close']:.2f}")
    except Exception as e:
        print(f"  [FAILED] {e}")

print("\n" + "=" * 70)
print("测试完成")
print("=" * 70)
