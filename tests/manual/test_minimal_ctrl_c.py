"""最小化测试 - 验证 Ctrl+C 能否工作"""
import sys
import time

print("=" * 60)
print("最小化测试：验证 Ctrl+C 响应")
print("=" * 60)
print("\n按 Ctrl+C 停止程序...\n")

try:
    counter = 0
    while True:
        counter += 1
        print(f"运行中... {counter} 秒", end='\r')
        time.sleep(1)
except KeyboardInterrupt:
    print("\n\n[SUCCESS] Ctrl+C 响应成功！")
    print("[INFO] 程序正常退出")
    sys.exit(0)
