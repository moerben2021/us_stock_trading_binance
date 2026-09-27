"""测试 Binance 资金账户 API 端点"""
import requests
import yaml
import time
import hmac
import hashlib
from urllib.parse import urlencode

# 读取配置
with open('system.yaml', 'r', encoding='utf-8') as f:
    system_config = yaml.safe_load(f)

with open('secrets/account1.key', 'r', encoding='utf-8') as f:
    secrets = yaml.safe_load(f)

api_key = secrets['binance']['api_key']
secret_key = secrets['binance']['secret_key']

# 代理设置
proxy_config = system_config.get("system", {}).get("proxy", {})
proxies = None
if proxy_config.get("enabled", False):
    proxies = {
        "http": proxy_config.get("http"),
        "https": proxy_config.get("https")
    }

def sign_request(params, secret):
    """签名请求"""
    query_string = urlencode(params)
    signature = hmac.new(
        secret.encode('utf-8'),
        query_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return signature

def test_endpoint(name, endpoint, params=None):
    """测试 API 端点"""
    print(f"\n{'='*60}")
    print(f"测试: {name}")
    print(f"端点: {endpoint}")
    print(f"{'='*60}")

    if params is None:
        params = {}

    # 添加时间戳
    params['timestamp'] = int(time.time() * 1000)

    # 签名
    signature = sign_request(params, secret_key)
    params['signature'] = signature

    # 请求
    url = f"https://api.binance.com{endpoint}"
    headers = {"X-MBX-APIKEY": api_key}

    try:
        response = requests.get(
            url,
            headers=headers,
            params=params,
            proxies=proxies,
            timeout=10
        )

        print(f"状态码: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"[SUCCESS] 成功!")
            # 显示数据结构而不是实际值
            if isinstance(data, list):
                print(f"返回列表，包含 {len(data)} 条记录")
                if len(data) > 0:
                    print(f"记录字段: {list(data[0].keys())}")
            elif isinstance(data, dict):
                print(f"返回字典，包含字段: {list(data.keys())}")
            else:
                print(f"返回类型: {type(data)}")
            return data
        else:
            print(f"[FAILED] 失败")
            print(f"错误: {response.text}")
            return None

    except Exception as e:
        print(f"[ERROR] 异常: {e}")
        return None

print("="*60)
print("Binance 资金账户 API 端点测试")
print("="*60)
print(f"代理: {proxies.get('http') if proxies else '直连'}")
print()

# 测试常见的资金账户端点
endpoints_to_test = [
    ("资金账户余额 v1", "/sapi/v1/asset/getUserAsset", {}),
    ("资金账户余额 v3", "/sapi/v3/asset/getUserAsset", {}),
    ("账户资产", "/sapi/v1/capital/config/getall", {}),
    ("现货账户信息", "/api/v3/account", {}),
    ("账户余额", "/sapi/v1/asset/get-funding-asset", {}),
    ("所有资产余额", "/sapi/v1/asset/assetBalance", {}),
]

print("\n开始测试各个端点...")

successful_endpoints = []

for name, endpoint, params in endpoints_to_test:
    result = test_endpoint(name, endpoint, params.copy())
    if result is not None:
        successful_endpoints.append((name, endpoint, result))
    time.sleep(1)  # 避免触发限流

print("\n" + "="*60)
print("测试总结")
print("="*60)

if successful_endpoints:
    print(f"\n[SUCCESS] 成功的端点 ({len(successful_endpoints)} 个):")
    for name, endpoint, data in successful_endpoints:
        print(f"\n{name}: {endpoint}")
        # 只显示数据结构，不显示实际值
        if isinstance(data, list):
            print(f"  数据类型: 列表 ({len(data)} 条记录)")
        elif isinstance(data, dict):
            print(f"  数据类型: 字典 (包含 {len(data)} 个字段)")
else:
    print("\n[FAILED] 没有成功的端点")

print("\n" + "="*60)
