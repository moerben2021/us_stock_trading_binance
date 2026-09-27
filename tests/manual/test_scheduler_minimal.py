"""最小化测试调度器"""
import time
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

def test_job():
    """测试任务"""
    now = datetime.now()
    print(f"[{now.strftime('%H:%M:%S')}] 测试任务执行!")

print("=" * 60)
print("最小化调度器测试")
print("=" * 60)
print()

# 创建调度器
scheduler = BackgroundScheduler(timezone="America/New_York")

# 获取当前美东时间
from datetime import timezone as tz
import pytz
et = pytz.timezone('America/New_York')
now_et = datetime.now(et)
print(f"当前美东时间: {now_et.strftime('%Y-%m-%d %H:%M:%S %Z')}")

# 设置任务在当前时间后 1 分钟执行
target_minute = (now_et.minute + 1) % 60
target_hour = now_et.hour
if target_minute == 0:
    target_hour = (target_hour + 1) % 24

trigger = CronTrigger(
    minute=target_minute,
    hour=target_hour,
    timezone="America/New_York"
)

scheduler.add_job(
    test_job,
    trigger=trigger,
    id="test_job",
    name="Test Job"
)

print(f"已注册任务: 将在 {target_hour:02d}:{target_minute:02d} 美东时间执行")
print()

# 启动调度器
scheduler.start()
print("调度器已启动")

# 显示所有任务
jobs = scheduler.get_jobs()
print(f"\n已注册的任务数量: {len(jobs)}")
for job in jobs:
    print(f"  - {job.id}: 下次运行 {job.next_run_time}")

print("\n等待任务执行 (2分钟)...")
print("按 Ctrl+C 停止")
print()

try:
    # 等待 2 分钟
    for i in range(120):
        time.sleep(1)
        if (i + 1) % 10 == 0:
            print(f"  已等待 {i+1} 秒...")
except KeyboardInterrupt:
    print("\n收到中断信号")
finally:
    scheduler.shutdown(wait=False)
    print("调度器已关闭")
