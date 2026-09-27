"""查询 Binance 支持的美股列表"""
import requests
import yaml

# 读取配置
with open('system.yaml', 'r', encoding='utf-8') as f:
    system_config = yaml.safe_load(f)

with open('secrets/account1.key', 'r', encoding='utf-8') as f:
    secrets = yaml.safe_load(f)

api_key = secrets['binance']['api_key']

# 代理设置
proxy_config = system_config.get("system", {}).get("proxy", {})
proxies = None
if proxy_config.get("enabled", False):
    proxies = {
        "http": proxy_config.get("http"),
        "https": proxy_config.get("https")
    }

print("=" * 60)
print("查询 Binance 支持的美股列表")
print("=" * 60)
print()

url = "https://api.binance.com/sapi/v1/equity/market/exchangeInfo"
headers = {"X-MBX-APIKEY": api_key}

try:
    response = requests.get(
        url,
        headers=headers,
        proxies=proxies,
        timeout=10
    )

    print(f"状态码: {response.status_code}")

    if response.status_code == 200:
        data = response.json()

        symbols = data.get("symbols", [])
        print(f"\n[SUCCESS] 获取到 {len(symbols)} 个可交易的美股")
        print()
        print("前 20 个股票:")
        for i, symbol in enumerate(symbols[:20], 1):
            ticker = symbol.get("symbol")
            status = symbol.get("status")
            print(f"  {i:2d}. {ticker:10s} - 状态: {status}")

        # 检查 SPY 是否在列表中
        spy_found = False
        for symbol in symbols:
            if symbol.get("symbol") == "SPY":
                spy_found = True
                print(f"\n[INFO] SPY 状态: {symbol.get('status')}")
                break

        if not spy_found:
            print(f"\n[WARNING] SPY 不在可交易列表中")

    else:
        print("[FAILED] 请求失败")
        print(f"错误代码: {response.status_code}")

except Exception as e:
    print(f"[ERROR] 错误: {str(e)}")

print()
print("=" * 60)
