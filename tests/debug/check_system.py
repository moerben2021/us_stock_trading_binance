"""系统完整性检查脚本"""
import sys
import os
from pathlib import Path

print("=" * 70)
print("US Stock DCA Framework - System Check")
print("=" * 70)

# 1. 检查关键文件
print("\n[1] Checking Critical Files:")
files_to_check = [
    "main.py",
    "system.yaml",
    "configs/accounts/account1.yaml",
    "secrets/account1.key",
    "database/schema.sql",
    "core/scheduler.py",
    "core/strategy_engine.py",
    "core/trade_executor.py",
    "integrations/binance_client.py",
    "integrations/yfinance_client.py",
    "integrations/wecom_notifier.py",
]

for f in files_to_check:
    exists = Path(f).exists()
    status = "OK" if exists else "MISSING"
    print(f"  {f}: {status}")

# 2. 检查配置
print("\n[2] Checking Configuration:")
try:
    import yaml
    with open("system.yaml", "r", encoding="utf-8") as f:
        system_config = yaml.safe_load(f)
    
    proxy_enabled = system_config.get("system", {}).get("proxy", {}).get("enabled", False)
    print(f"  Proxy enabled: {proxy_enabled}")
    
    with open("configs/accounts/account1.yaml", "r", encoding="utf-8") as f:
        account_config = yaml.safe_load(f)
    
    webhook = account_config.get("account", {}).get("wecom_webhook")
    strategies_count = len(account_config.get("strategies", []))
    print(f"  WeChat webhook configured: {'YES' if webhook else 'NO'}")
    print(f"  Strategies configured: {strategies_count}")
    
except Exception as e:
    print(f"  ERROR: {e}")

# 3. 检查数据库
print("\n[3] Checking Database:")
db_path = Path("data/trading.db")
if db_path.exists():
    import sqlite3
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 检查表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"  Database exists: OK")
    print(f"  Tables: {len(tables)}")
    for table in tables:
        print(f"    - {table[0]}")
    
    conn.close()
else:
    print(f"  Database exists: NO (will be created on first run)")

# 4. 检查依赖
print("\n[4] Checking Dependencies:")
dependencies = [
    "yaml", "requests", "apscheduler", "pandas", "yfinance", "pytz"
]

for dep in dependencies:
    try:
        __import__(dep)
        print(f"  {dep}: OK")
    except ImportError:
        print(f"  {dep}: MISSING")

print("\n" + "=" * 70)
print("Check Complete")
print("=" * 70)
