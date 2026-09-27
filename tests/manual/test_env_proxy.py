"""测试环境变量代理"""
import os
import yaml
from integrations.yfinance_client import YFinanceClient

print("=" * 70)
print("测试环境变量代理")
print("=" * 70)

# 1. 加载系统配置并设置环境变量
print("\n[步骤 1] 设置环境变量代理")
print("-" * 70)
with open("system.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

proxy_config = config.get("system", {}).get("proxy", {})
proxy_enabled = proxy_config.get("enabled", False)

if proxy_enabled:
    http_proxy = proxy_config.get("http")
    https_proxy = proxy_config.get("https")

    os.environ["HTTP_PROXY"] = http_proxy
    os.environ["HTTPS_PROXY"] = https_proxy
    os.environ["http_proxy"] = http_proxy
    os.environ["https_proxy"] = https_proxy

    print(f"已设置环境变量:")
    print(f"  HTTP_PROXY={http_proxy}")
    print(f"  HTTPS_PROXY={https_proxy}")
else:
    print("代理未启用")

# 2. 验证环境变量
print("\n[步骤 2] 验证环境变量")
print("-" * 70)
print(f"HTTP_PROXY: {os.environ.get('HTTP_PROXY')}")
print(f"HTTPS_PROXY: {os.environ.get('HTTPS_PROXY')}")
print(f"http_proxy: {os.environ.get('http_proxy')}")
print(f"https_proxy: {os.environ.get('https_proxy')}")

# 3. 创建 yFinance 客户端
print("\n[步骤 3] 创建 yFinance 客户端")
print("-" * 70)
client = YFinanceClient()

# 4. 测试获取历史数据
print("\n[步骤 4] 测试获取历史数据")
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
        import traceback
        traceback.print_exc()

print("\n" + "=" * 70)
print("测试完成")
print("=" * 70)
