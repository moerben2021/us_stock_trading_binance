"""测试多个可能的资金账户余额 API 端点"""
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

def test_endpoint(name, endpoint, method="GET", extra_params=None):
    """测试 API 端点"""
    print(f"\n{'='*60}")
    print(f"测试: {name}")
    print(f"端点: {method} {endpoint}")
    print(f"{'='*60}")

    params = {"timestamp": int(time.time() * 1000)}
    if extra_params:
        params.update(extra_params)

    # 签名
    signature = sign_request(params, secret_key)
    params['signature'] = signature

    url = f"https://api.binance.com{endpoint}"
    headers = {"X-MBX-APIKEY": api_key}

    try:
        if method == "GET":
            response = requests.get(url, headers=headers, params=params, proxies=proxies, timeout=10)
        else:
            response = requests.post(url, headers=headers, params=params, proxies=proxies, timeout=10)

        print(f"状态码: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"[SUCCESS] 成功!")

            # 显示数据结构
            if isinstance(data, list):
                print(f"返回列表，包含 {len(data)} 条记录")
                if len(data) > 0:
                    print(f"第一条记录字段: {list(data[0].keys())}")
                    # 查找 USDC
                    for item in data:
                        if item.get('asset') == 'USDC' or item.get('coin') == 'USDC':
                            print(f"\n[FOUND] USDC 余额:")
                            for key, value in item.items():
                                print(f"  {key}: {value}")
                            break
            elif isinstance(data, dict):
                print(f"返回字典，包含字段: {list(data.keys())}")
                # 查找余额相关字段
                if 'balances' in data:
                    balances = data['balances']
                    print(f"balances 包含 {len(balances)} 条记录")
                    for item in balances:
                        if item.get('asset') == 'USDC' or item.get('coin') == 'USDC':
                            print(f"\n[FOUND] USDC 余额:")
                            for key, value in item.items():
                                print(f"  {key}: {value}")
                            break
            return True
        else:
            print(f"[FAILED] 失败")
            try:
                error = response.json()
                print(f"错误码: {error.get('code')}")
                print(f"错误信息: {error.get('msg')}")
            except:
                print(f"HTTP 错误码: {response.status_code}")
            return False

    except Exception as e:
        print(f"[ERROR] 异常: {str(e)}")
        return False

print("=" * 60)
print("查找资金账户余额 API")
print("=" * 60)

# 测试可能的资金账户端点
endpoints_to_test = [
    ("资金账户余额", "/sapi/v1/asset/get-funding-asset", "POST", {}),
    ("账户快照 - 现货", "/sapi/v1/accountSnapshot", "GET", {"type": "SPOT"}),
    ("账户快照 - 资金", "/sapi/v1/accountSnapshot", "GET", {"type": "FUNDING"}),
    ("资金钱包", "/sapi/v1/asset/wallet/balance", "GET", {}),
    ("所有币种信息", "/sapi/v1/capital/config/getall", "GET", {}),
    ("现货账户信息", "/api/v3/account", "GET", {}),
    ("资金账户余额 v3", "/sapi/v3/asset/getUserAsset", "POST", {}),
]

successful = []

for name, endpoint, method, params in endpoints_to_test:
    if test_endpoint(name, endpoint, method, params):
        successful.append((name, endpoint))
    time.sleep(1)  # 避免限流

print("\n" + "=" * 60)
print("测试总结")
print("=" * 60)

if successful:
    print(f"\n[SUCCESS] 成功的端点 ({len(successful)} 个):")
    for name, endpoint in successful:
        print(f"  - {name}: {endpoint}")
else:
    print("\n[FAILED] 没有成功的端点")

print("\n" + "=" * 60)
