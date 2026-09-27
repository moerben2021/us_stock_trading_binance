"""直接测试 Binance 美股报价 API"""
import requests
import yaml

# 读取 API 密钥
with open('secrets/account1.key', 'r', encoding='utf-8') as f:
    secrets = yaml.safe_load(f)

api_key = secrets['binance']['api_key']

# 测试报价端点
url = "https://api.binance.com/sapi/v1/equity/market/quote"
headers = {
    "X-MBX-APIKEY": api_key
}
params = {
    "symbol": "SPY"
}

# 使用代理
proxies = {
    "http": "http://127.0.0.1:7990",
    "https": "http://127.0.0.1:7990"
}

print("=" * 60)
print("测试 Binance 美股报价 API")
print("=" * 60)
print(f"URL: {url}")
print(f"Symbol: SPY")
print(f"API Key: [REDACTED]")
print(f"代理: {proxies['http']}")
print()

try:
    response = requests.get(
        url,
        headers=headers,
        params=params,
        proxies=proxies,
        timeout=10
    )

    print(f"状态码: {response.status_code}")
    print(f"响应头: {dict(response.headers)}")
    print()

    if response.status_code == 200:
        data = response.json()
        print("[SUCCESS] 成功获取报价!")
        print(f"响应数据: {data}")

        if 'bidPrice' in data and 'askPrice' in data:
            bid = float(data['bidPrice'])
            ask = float(data['askPrice'])
            mid = (bid + ask) / 2
            print()
            print(f"买价: ${bid:.2f}")
            print(f"卖价: ${ask:.2f}")
            print(f"中间价: ${mid:.2f}")
    else:
        print("[FAILED] 请求失败")
        print(f"错误信息: {response.text}")

except Exception as e:
    print(f"[ERROR] 异常: {e}")
    import traceback
    traceback.print_exc()
