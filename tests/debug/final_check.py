"""最终检查：查找潜在问题"""
import re
from pathlib import Path

print("=" * 70)
print("Final System Check - Potential Issues")
print("=" * 70)

issues = []

# 1. 检查是否有硬编码的敏感信息
print("\n[1] Checking for hardcoded secrets...")
sensitive_patterns = [
    (r'api_key\s*=\s*["\'][^"\']+["\']', "Hardcoded API key"),
    (r'secret_key\s*=\s*["\'][^"\']+["\']', "Hardcoded secret key"),
    (r'webhook.*=.*https://qyapi\.weixin\.qq\.com', "Hardcoded webhook (acceptable in config)"),
]

py_files = list(Path('.').glob('**/*.py'))
py_files = [f for f in py_files if '__pycache__' not in str(f) and 'test_' not in str(f)]

for py_file in py_files[:10]:  # 只检查主要文件
    try:
        content = py_file.read_text(encoding='utf-8')
        for pattern, desc in sensitive_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                if 'config' not in str(py_file) and 'test' not in str(py_file):
                    print(f"  WARNING: {py_file} - {desc}")
    except:
        pass

# 2. 检查错误处理
print("\n[2] Checking error handling...")
critical_files = [
    'core/trade_executor.py',
    'integrations/binance_client.py',
    'integrations/wecom_notifier.py'
]

for file in critical_files:
    try:
        content = Path(file).read_text(encoding='utf-8')
        # 检查是否有裸 except
        bare_excepts = len(re.findall(r'except\s*:', content))
        if bare_excepts > 0:
            print(f"  INFO: {file} has {bare_excepts} bare except (acceptable if logging)")
    except:
        pass

# 3. 检查日志记录
print("\n[3] Checking logging...")
for file in critical_files:
    try:
        content = Path(file).read_text(encoding='utf-8')
        has_logger = 'logger = logging.getLogger' in content
        print(f"  {file}: {'OK' if has_logger else 'NO LOGGER'}")
    except:
        pass

# 4. 检查配置一致性
print("\n[4] Checking configuration consistency...")
try:
    import yaml
    
    # 系统配置
    with open('system.yaml', 'r', encoding='utf-8') as f:
        sys_config = yaml.safe_load(f)
    
    proxy = sys_config.get('system', {}).get('proxy', {})
    print(f"  Proxy enabled: {proxy.get('enabled')}")
    print(f"  Proxy URL: {proxy.get('http', 'Not set')}")
    
    # 账户配置
    with open('configs/accounts/account1.yaml', 'r', encoding='utf-8') as f:
        acc_config = yaml.safe_load(f)
    
    webhook = acc_config.get('account', {}).get('wecom_webhook')
    print(f"  Webhook configured: {'YES' if webhook else 'NO'}")
    
    strategies = acc_config.get('strategies', [])
    for strat in strategies:
        status = strat.get('status', 'unknown')
        if status != 'active':
            print(f"  WARNING: Strategy {strat.get('id')} is {status}")
    
except Exception as e:
    print(f"  ERROR: {e}")

# 5. 检查时区设置
print("\n[5] Checking timezone configuration...")
try:
    import yaml
    with open('system.yaml', 'r', encoding='utf-8') as f:
        sys_config = yaml.safe_load(f)
    
    tz = sys_config.get('system', {}).get('timezone', 'Not set')
    print(f"  System timezone: {tz}")
    
    with open('configs/accounts/account1.yaml', 'r', encoding='utf-8') as f:
        acc_config = yaml.safe_load(f)
    
    strategies = acc_config.get('strategies', [])
    print(f"  Strategies with schedules: {len(strategies)}")
    for strat in strategies[:3]:
        print(f"    - {strat.get('id')}: {strat.get('schedule')}")
    
except Exception as e:
    print(f"  ERROR: {e}")

print("\n" + "=" * 70)
print("Final Check Complete")
print("=" * 70)
