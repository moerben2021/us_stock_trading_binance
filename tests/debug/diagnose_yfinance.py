"""系统诊断 yFinance 问题"""
import sys
import os
import requests
import yfinance as yf
from datetime import datetime, timedelta
import yaml

print("=" * 70)
print("yFinance 问题诊断")
print("=" * 70)

# 1. 检查代理配置
print("\n[步骤 1] 检查系统代理配置")
print("-" * 70)
with open("system.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

proxy_enabled = config.get("system", {}).get("proxy", {}).get("enabled", False)
proxy_http = config.get("system", {}).get("proxy", {}).get("http")
proxy_https = config.get("system", {}).get("proxy", {}).get("https")

print(f"代理启用: {proxy_enabled}")
print(f"HTTP 代理: {proxy_http}")
print(f"HTTPS 代理: {proxy_https}")

if proxy_enabled:
    proxies = {"http": proxy_http, "https": proxy_https}
    print(f"将使用代理: {proxies}")
else:
    proxies = None
    print("未启用代理")

# 2. 测试代理连通性
print("\n[步骤 2] 测试代理连通性")
print("-" * 70)

test_urls = [
    "https://www.google.com",
    "https://query2.finance.yahoo.com",
]

for url in test_urls:
    try:
        print(f"\n测试: {url}")
        response = requests.get(url, proxies=proxies, timeout=10)
        print(f"  [SUCCESS] 状态码: {response.status_code}")
    except Exception as e:
        print(f"  [FAILED] {e}")

# 3. 检查环境变量代理设置
print("\n[步骤 3] 检查环境变量代理设置")
print("-" * 70)
env_proxies = {
    "HTTP_PROXY": os.environ.get("HTTP_PROXY"),
    "HTTPS_PROXY": os.environ.get("HTTPS_PROXY"),
    "http_proxy": os.environ.get("http_proxy"),
    "https_proxy": os.environ.get("https_proxy"),
}
print(f"环境变量: {env_proxies}")

# 4. yFinance 直接测试（不经过我们的封装）
print("\n[步骤 4] yFinance 原生 API 测试")
print("-" * 70)

# 测试 A: 使用 period 参数
print("\n测试 A: ticker.history(period='1mo')")
try:
    ticker = yf.Ticker("SPY")
    data = ticker.history(period="1mo")
    if data.empty:
        print("  [WARNING] 返回空数据")
    else:
        print(f"  [SUCCESS] 获取 {len(data)} 条数据")
        print(f"  日期范围: {data.index[0]} 到 {data.index[-1]}")
except Exception as e:
    print(f"  [FAILED] {e}")

# 测试 B: 使用 start/end 参数
print("\n测试 B: ticker.history(start=..., end=...)")
try:
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    print(f"  start_date: {start_date}")
    print(f"  end_date: {end_date}")

    ticker = yf.Ticker("SPY")
    data = ticker.history(start=start_date, end=end_date)
    if data.empty:
        print("  [WARNING] 返回空数据")
    else:
        print(f"  [SUCCESS] 获取 {len(data)} 条数据")
        print(f"  日期范围: {data.index[0]} 到 {data.index[-1]}")
except Exception as e:
    print(f"  [FAILED] {e}")

# 测试 C: 使用 download 函数
print("\n测试 C: yf.download('SPY', period='1mo')")
try:
    data = yf.download("SPY", period="1mo", progress=False)
    if data.empty:
        print("  [WARNING] 返回空数据")
    else:
        print(f"  [SUCCESS] 获取 {len(data)} 条数据")
        print(f"  日期范围: {data.index[0]} 到 {data.index[-1]}")
except Exception as e:
    print(f"  [FAILED] {e}")

# 5. 检查 yFinance 是否使用代理
print("\n[步骤 5] yFinance 代理使用情况")
print("-" * 70)
print("yFinance 默认使用 requests 库，会自动读取环境变量代理")
print("如果环境变量没有设置代理，yFinance 会直连 Yahoo Finance")

if env_proxies.get("http_proxy") or env_proxies.get("https_proxy"):
    print("[INFO] 环境变量已设置代理，yFinance 会使用代理")
else:
    print("[WARNING] 环境变量未设置代理，yFinance 不会使用代理")
    if proxy_enabled:
        print("[WARNING] 虽然 system.yaml 启用了代理，但环境变量未设置")
        print("[WARNING] 需要在启动前设置环境变量或修改 yFinance 调用方式")

print("\n" + "=" * 70)
print("诊断完成")
print("=" * 70)
