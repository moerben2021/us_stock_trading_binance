"""API 限流器"""
import time
import threading
from collections import deque
from typing import Deque

class RateLimiter:
    """
    API 请求限流器
    使用滑动窗口算法控制请求频率
    """

    def __init__(self, max_requests_per_minute: int = 1200, max_requests_per_second: int = 20):
        """
        初始化限流器

        Args:
            max_requests_per_minute: 每分钟最大请求数
            max_requests_per_second: 每秒最大请求数
        """
        self.max_per_minute = max_requests_per_minute
        self.max_per_second = max_requests_per_second

        self.minute_window: Deque[float] = deque()
        self.second_window: Deque[float] = deque()

        self.lock = threading.Lock()

    def acquire(self):
        """
        获取请求许可
        如果超过限制，会阻塞等待
        """
        while True:
            with self.lock:
                now = time.time()

                # 清理过期的时间戳（1分钟窗口）
                while self.minute_window and now - self.minute_window[0] > 60:
                    self.minute_window.popleft()

                # 清理过期的时间戳（1秒窗口）
                while self.second_window and now - self.second_window[0] > 1:
                    self.second_window.popleft()

                # 检查是否需要等待
                wait_time = 0

                # 检查每分钟限制
                if len(self.minute_window) >= self.max_per_minute:
                    oldest = self.minute_window[0]
                    wait_time = max(wait_time, 60 - (now - oldest))

                # 检查每秒限制
                if len(self.second_window) >= self.max_per_second:
                    oldest = self.second_window[0]
                    wait_time = max(wait_time, 1 - (now - oldest))

                # 如果不需要等待，记录请求并返回
                if wait_time <= 0:
                    self.minute_window.append(now)
                    self.second_window.append(now)
                    return

            # 在锁外等待，不阻塞其他线程
            time.sleep(wait_time)
