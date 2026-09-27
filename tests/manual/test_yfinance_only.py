"""专门测试 yFinance 代理和数据获取"""
import sys
import os
from pathlib import Path

# 添加项目根目录到 sys.path
sys.path.insert(0, str(Path(__file__).parent))

# ============================================================
# 关键：在导入任何模块之前，先设置环境变量代理
# ============================================================
import yaml

system_yaml_path = Path(__file__).parent / "system.yaml"
if system_yaml_path.exists():
    with open(system_yaml_path, "r", encoding="utf-8") as f:
        _system_config = yaml.safe_load(f)

    _proxy_config = _system_config.get("system", {}).get("proxy", {})
    _proxy_enabled = _proxy_config.get("enabled", False)

    if _proxy_enabled:
        _http_proxy = _proxy_config.get("http")
        _https_proxy = _proxy_config.get("https")

        os.environ["HTTP_PROXY"] = _http_proxy
        os.environ["HTTPS_PROXY"] = _https_proxy
        os.environ["http_proxy"] = _http_proxy
        os.environ["https_proxy"] = _https_proxy

        print(f"[OK] 环境变量已设置: {_http_proxy}")

# 现在可以导入 yfinance
from integrations.yfinance_client import YFinanceClient

print("\n" + "=" * 70)
print("yFinance 代理测试")
print("=" * 70)

# 验证环境变量
print("\n[环境变量验证]")
print(f"HTTP_PROXY: {os.environ.get('HTTP_PROXY')}")
print(f"HTTPS_PROXY: {os.environ.get('HTTPS_PROXY')}")

# 创建 yFinance 客户端
print("\n[创建 yFinance 客户端]")
client = YFinanceClient()

# 测试获取历史数据
print("\n[测试历史数据获取]")
print("-" * 70)

symbols = ["SPY", "QQQ"]

for symbol in symbols:
    print(f"\n测试 {symbol}:")
    print(f"  请求最近 30 天的历史数据...")

    try:
        data = client.get_history_data(symbol, 30)

        if data.empty:
            print(f"  [FAILED] 返回空数据")
            print(f"     原因：可能是周末无数据或 API 限流")
        else:
            print(f"  [SUCCESS] 成功获取 {len(data)} 条数据")
            print(f"  [SUCCESS] 日期范围: {data.index[0]} 到 {data.index[-1]}")
            print(f"  [SUCCESS] 最新收盘价: ${data.iloc[-1]['Close']:.2f}")

            # 显示最近 3 天数据
            print(f"\n  最近 3 天数据:")
            for idx in range(max(0, len(data) - 3), len(data)):
                row = data.iloc[idx]
                print(f"    {data.index[idx].date()}: "
                      f"开盘 ${row['Open']:.2f}, "
                      f"收盘 ${row['Close']:.2f}, "
                      f"成交量 {row['Volume']:,.0f}")

    except Exception as e:
        print(f"  [FAILED] 异常: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 70)
print("测试完成")
print("=" * 70)

# 总结
print("\n[总结]")
print("如果看到：")
print("  [SUCCESS] 成功获取数据 -> 代理工作正常，yFinance 修复成功")
print("  [FAILED] 返回空数据 -> 可能是周末无数据（正常现象）")
print("  [FAILED] 连接错误 -> 代理问题")
