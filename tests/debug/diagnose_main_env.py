"""诊断环境变量是否在 main.py 中生效"""
import os
import sys
from pathlib import Path

# 添加项目根目录到 sys.path
sys.path.insert(0, str(Path(__file__).parent))

from config.loader import ConfigLoader

print("=" * 70)
print("诊断 main.py 环境变量")
print("=" * 70)

# 1. 启动前检查环境变量
print("\n[启动前] 环境变量状态:")
print("-" * 70)
print(f"HTTP_PROXY: {os.environ.get('HTTP_PROXY', '未设置')}")
print(f"HTTPS_PROXY: {os.environ.get('HTTPS_PROXY', '未设置')}")
print(f"http_proxy: {os.environ.get('http_proxy', '未设置')}")
print(f"https_proxy: {os.environ.get('https_proxy', '未设置')}")

# 2. 加载配置
print("\n[步骤 1] 加载系统配置")
print("-" * 70)
config_loader = ConfigLoader()
system_config = config_loader.load_system_config()

proxy_config = system_config.get("system", {}).get("proxy", {})
proxy_enabled = proxy_config.get("enabled", False)

print(f"system.yaml 代理配置:")
print(f"  enabled: {proxy_enabled}")
print(f"  http: {proxy_config.get('http', '未配置')}")
print(f"  https: {proxy_config.get('https', '未配置')}")

# 3. 模拟 main.py 的逻辑设置环境变量
print("\n[步骤 2] 设置环境变量（模拟 main.py）")
print("-" * 70)

proxies = None
if proxy_enabled:
    proxies = {
        "http": proxy_config.get("http"),
        "https": proxy_config.get("https")
    }
    # 设置环境变量，让 yFinance 使用代理
    os.environ["HTTP_PROXY"] = proxies["http"]
    os.environ["HTTPS_PROXY"] = proxies["https"]
    os.environ["http_proxy"] = proxies["http"]
    os.environ["https_proxy"] = proxies["https"]
    print(f"已设置环境变量: {proxies['http']}")
else:
    print("代理未启用，未设置环境变量")

# 4. 设置后检查环境变量
print("\n[设置后] 环境变量状态:")
print("-" * 70)
print(f"HTTP_PROXY: {os.environ.get('HTTP_PROXY', '未设置')}")
print(f"HTTPS_PROXY: {os.environ.get('HTTPS_PROXY', '未设置')}")
print(f"http_proxy: {os.environ.get('http_proxy', '未设置')}")
print(f"https_proxy: {os.environ.get('https_proxy', '未设置')}")

# 5. 测试 yFinance
print("\n[步骤 3] 测试 yFinance 是否使用代理")
print("-" * 70)

from integrations.yfinance_client import YFinanceClient

client = YFinanceClient()
print("yFinance 客户端已创建")

print("\n测试获取 SPY 数据:")
data = client.get_history_data("SPY", 30)

if data.empty:
    print("  [FAILED] 返回空数据")
else:
    print(f"  [SUCCESS] 获取 {len(data)} 条数据")
    print(f"  日期范围: {data.index[0]} 到 {data.index[-1]}")

print("\n" + "=" * 70)
print("诊断完成")
print("=" * 70)
