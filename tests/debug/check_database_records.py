"""检查数据库记录完整性"""
import sqlite3
from pathlib import Path

db_path = Path("data/trading.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=" * 70)
print("Database Records Completeness Check")
print("=" * 70)

# 1. 检查所有表的记录数
print("\n[1] Record Count by Table:")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [row[0] for row in cursor.fetchall()]

for table in tables:
    if table != 'sqlite_sequence':
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  {table}: {count}")

# 2. 检查最近的策略执行记录
print("\n[2] Recent Strategy Executions:")
cursor.execute("""
    SELECT id, account_name, strategy_id, signal, status, executed_at 
    FROM strategy_executions 
    ORDER BY executed_at DESC 
    LIMIT 5
""")
for row in cursor.fetchall():
    print(f"  ID={row[0]}, Strategy={row[2]}, Signal={row[3]}, Status={row[4]}")

# 3. 检查交易记录
print("\n[3] Trade Records:")
cursor.execute("""
    SELECT id, account_name, symbol, action, quantity, amount, executed_at
    FROM trades
    ORDER BY executed_at DESC
    LIMIT 5
""")
for row in cursor.fetchall():
    print(f"  ID={row[0]}, Symbol={row[2]}, Action={row[3]}, Qty={row[4]}, Amt={row[5]}")

# 4. 检查持仓记录
print("\n[4] Positions:")
cursor.execute("SELECT account_name, symbol, quantity, avg_cost, updated_at FROM positions")
for row in cursor.fetchall():
    print(f"  {row[0]}/{row[1]}: Qty={row[2]}, AvgCost={row[3]}")

# 5. 检查账户快照
print("\n[5] Account Snapshots:")
cursor.execute("SELECT COUNT(*) FROM account_snapshots")
count = cursor.fetchone()[0]
if count == 0:
    print("  NO RECORDS - Account snapshots are not being saved!")
else:
    cursor.execute("SELECT account_name, snapshot_type, snapshot_at FROM account_snapshots ORDER BY snapshot_at DESC LIMIT 3")
    for row in cursor.fetchall():
        print(f"  {row[0]}, Type={row[1]}, At={row[2]}")

# 6. 检查通知记录
print("\n[6] Notifications:")
cursor.execute("SELECT COUNT(*) FROM notifications")
count = cursor.fetchone()[0]
if count == 0:
    print("  NO RECORDS - Will be saved after next notification (fixed)")
else:
    cursor.execute("SELECT account_name, notification_type, sent_at FROM notifications ORDER BY sent_at DESC LIMIT 3")
    for row in cursor.fetchall():
        print(f"  {row[0]}, Type={row[1]}, At={row[2]}")

conn.close()

print("\n" + "=" * 70)
print("Analysis:")
print("=" * 70)
print("Missing Records:")
print("  1. account_snapshots: 0 records")
print("     - Should save daily/periodic snapshots of account balance & positions")
print("  2. notifications: 0 records")
print("     - Fixed: will be saved after restart")
print("=" * 70)
