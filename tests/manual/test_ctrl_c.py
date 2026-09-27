"""测试 Ctrl+C 信号处理"""
import signal
import sys
import time

def signal_handler(signum, frame):
    print(f"\n[INFO] 收到信号 {signum}")
    print("[INFO] 程序正在退出...")
    sys.exit(0)

# 注册信号处理器
signal.signal(signal.SIGINT, signal_handler)

print("测试程序已启动")
print("按 Ctrl+C 测试信号处理...")
print()

# 模拟阻塞操作
counter = 0
while True:
    counter += 1
    print(f"运行中... {counter} 秒", end='\r')
    time.sleep(1)
