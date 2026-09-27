"""测试调度器 Ctrl+C 响应"""
import time
from apscheduler.schedulers.background import BackgroundScheduler

print("测试 BackgroundScheduler 的 Ctrl+C 响应")
print("=" * 60)

# 创建后台调度器
scheduler = BackgroundScheduler()

# 添加一个简单的测试任务
def test_job():
    print(f"[{time.strftime('%H:%M:%S')}] 测试任务执行")

scheduler.add_job(test_job, 'interval', seconds=5, id='test_job')

# 启动调度器
scheduler.start()
print("[OK] 调度器已启动")
print("\n已注册任务:")
for job in scheduler.get_jobs():
    print(f"  - {job.id}: 下次运行 {job.next_run_time}")

print("\n按 Ctrl+C 停止...\n")

# 主线程保持运行
try:
    counter = 0
    while True:
        counter += 1
        print(f"运行中... {counter} 秒", end='\r')
        time.sleep(1)
except KeyboardInterrupt:
    print("\n\n[INFO] 收到 Ctrl+C，正在停止...")
    scheduler.shutdown(wait=False)
    print("[INFO] 调度器已停止")
    print("[INFO] 测试成功！")
