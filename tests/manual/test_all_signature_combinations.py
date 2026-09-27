"""系统测试所有可能的签名方式组合"""
import hmac
import hashlib
import time
import requests
from pathlib import Path
import yaml

# 加载密钥
secrets_file = Path("secrets/account1.key")
with open(secrets_file, "r") as f:
    secrets = yaml.safe_load(f)

binance_config = secrets.get("binance", {})
api_key = binance_config.get("api_key")
secret_key = binance_config.get("secret_key")

base_url = "https://api.binance.com"
endpoint = "/sapi/v1/equity/order/place"
proxies = {"http": "http://127.0.0.1:7990", "https": "http://127.0.0.1:7990"}

print("=" * 80)
print("系统测试所有可能的签名方式")
print("=" * 80)

test_cases = []

# 获取 Binance 服务器时间
try:
    time_response = requests.get(base_url + "/api/v3/time", proxies=proxies, timeout=10)
    server_time = time_response.json().get("serverTime")
    print(f"\nBinance 服务器时间: {server_time}")
except:
    server_time = int(time.time() * 1000)
    print(f"\n使用本地时间: {server_time}")

# 测试组合：
# 1. 参数类型：notional 整数 vs 字符串 vs 浮点数
# 2. 参数顺序：排序 vs 不排序
# 3. 请求方式：params vs data

# === 组合 1: notional=6 (整数), 排序, params ===
print(f"\n{'='*80}")
print("[组合 1] notional=6 (整数), 参数排序, 使用 params")
print("-" * 80)

params = {
    "symbol": "SPY",
    "side": "BUY",
    "orderType": "MARKET",
    "notional": 6,
    "timestamp": server_time
}

query_string = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
signature = hmac.new(secret_key.encode("utf-8"), query_string.encode("utf-8"), hashlib.sha256).hexdigest()
params["signature"] = signature

print(f"Query: {query_string}")

try:
    response = requests.post(base_url + endpoint, params=params,
                           headers={"X-MBX-APIKEY": api_key}, proxies=proxies, timeout=10)

    if response.status_code == 200:
        print("✅ 成功!")
        test_cases.append(("组合 1", "SUCCESS"))
    else:
        error = response.json()
        msg = error.get('msg', '')
        if 'suspended' in msg.lower() or 'closed' in msg.lower():
            print(f"✅ 签名通过（市场关闭）: {msg}")
            test_cases.append(("组合 1", "PASS"))
        else:
            print(f"❌ 失败: code={error.get('code')}, msg={msg}")
            test_cases.append(("组合 1", "FAIL"))
except Exception as e:
    print(f"❌ 异常: {e}")
    test_cases.append(("组合 1", "ERROR"))

# === 组合 2: notional="6" (字符串), 排序, params ===
print(f"\n{'='*80}")
print("[组合 2] notional='6' (字符串), 参数排序, 使用 params")
print("-" * 80)

params = {
    "symbol": "SPY",
    "side": "BUY",
    "orderType": "MARKET",
    "notional": "6",
    "timestamp": server_time
}

query_string = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
signature = hmac.new(secret_key.encode("utf-8"), query_string.encode("utf-8"), hashlib.sha256).hexdigest()
params["signature"] = signature

print(f"Query: {query_string}")

try:
    response = requests.post(base_url + endpoint, params=params,
                           headers={"X-MBX-APIKEY": api_key}, proxies=proxies, timeout=10)

    if response.status_code == 200:
        print("✅ 成功!")
        test_cases.append(("组合 2", "SUCCESS"))
    else:
        error = response.json()
        msg = error.get('msg', '')
        if 'suspended' in msg.lower() or 'closed' in msg.lower():
            print(f"✅ 签名通过（市场关闭）: {msg}")
            test_cases.append(("组合 2", "PASS"))
        else:
            print(f"❌ 失败: code={error.get('code')}, msg={msg}")
            test_cases.append(("组合 2", "FAIL"))
except Exception as e:
    print(f"❌ 异常: {e}")
    test_cases.append(("组合 2", "ERROR"))

# === 组合 3: notional=6 (整数), 不排序, params ===
print(f"\n{'='*80}")
print("[组合 3] notional=6 (整数), 参数不排序, 使用 params")
print("-" * 80)

param_list = [
    ("symbol", "SPY"),
    ("side", "BUY"),
    ("orderType", "MARKET"),
    ("notional", 6),
    ("timestamp", server_time)
]

query_string = "&".join([f"{k}={v}" for k, v in param_list])
signature = hmac.new(secret_key.encode("utf-8"), query_string.encode("utf-8"), hashlib.sha256).hexdigest()
param_list.append(("signature", signature))

print(f"Query: {query_string}")

try:
    response = requests.post(base_url + endpoint, params=param_list,
                           headers={"X-MBX-APIKEY": api_key}, proxies=proxies, timeout=10)

    if response.status_code == 200:
        print("✅ 成功!")
        test_cases.append(("组合 3", "SUCCESS"))
    else:
        error = response.json()
        msg = error.get('msg', '')
        if 'suspended' in msg.lower() or 'closed' in msg.lower():
            print(f"✅ 签名通过（市场关闭）: {msg}")
            test_cases.append(("组合 3", "PASS"))
        else:
            print(f"❌ 失败: code={error.get('code')}, msg={msg}")
            test_cases.append(("组合 3", "FAIL"))
except Exception as e:
    print(f"❌ 异常: {e}")
    test_cases.append(("组合 3", "ERROR"))

# === 组合 4: notional=6, 排序, data ===
print(f"\n{'='*80}")
print("[组合 4] notional=6 (整数), 参数排序, 使用 data (body)")
print("-" * 80)

params = {
    "symbol": "SPY",
    "side": "BUY",
    "orderType": "MARKET",
    "notional": 6,
    "timestamp": server_time
}

query_string = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
signature = hmac.new(secret_key.encode("utf-8"), query_string.encode("utf-8"), hashlib.sha256).hexdigest()
params["signature"] = signature

print(f"Body: {query_string}")

try:
    response = requests.post(base_url + endpoint, data=params,
                           headers={"X-MBX-APIKEY": api_key, "Content-Type": "application/x-www-form-urlencoded"},
                           proxies=proxies, timeout=10)

    if response.status_code == 200:
        print("✅ 成功!")
        test_cases.append(("组合 4", "SUCCESS"))
    else:
        error = response.json()
        msg = error.get('msg', '')
        if 'suspended' in msg.lower() or 'closed' in msg.lower():
            print(f"✅ 签名通过（市场关闭）: {msg}")
            test_cases.append(("组合 4", "PASS"))
        else:
            print(f"❌ 失败: code={error.get('code')}, msg={msg}")
            test_cases.append(("组合 4", "FAIL"))
except Exception as e:
    print(f"❌ 异常: {e}")
    test_cases.append(("组合 4", "ERROR"))

# === 总结 ===
print(f"\n{'='*80}")
print("测试结果总结")
print("=" * 80)

success_found = False
for name, result in test_cases:
    symbol = "✅" if result in ["SUCCESS", "PASS"] else "❌"
    print(f"{symbol} {name}: {result}")
    if result in ["SUCCESS", "PASS"]:
        success_found = True

if success_found:
    print("\n✅ 找到了正确的签名方式！")
else:
    print("\n❌ 所有组合都失败了")
    print("\n可能的原因:")
    print("  1. API Key 确实没有股票交易权限")
    print("  2. 账户需要额外的股票交易激活步骤")
    print("  3. 存在其他未知的参数要求")
    print("\n建议:")
    print("  - 检查之前成功的代码实现")
    print("  - 联系 Binance 客服确认股票交易权限状态")

print("=" * 80)
