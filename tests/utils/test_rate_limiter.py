import pytest
import time
from utils.rate_limiter import RateLimiter

def test_rate_limiter_allows_within_limit():
    """测试限流器允许限制内的请求"""
    limiter = RateLimiter(max_requests_per_minute=60, max_requests_per_second=10)

    # 快速发起5个请求，应该都被允许
    for _ in range(5):
        limiter.acquire()  # 不应该阻塞

def test_rate_limiter_blocks_when_exceeds():
    """测试限流器阻塞超出限制的请求"""
    limiter = RateLimiter(max_requests_per_minute=60, max_requests_per_second=2)

    # 快速发起3个请求
    start = time.time()
    for _ in range(3):
        limiter.acquire()
    elapsed = time.time() - start

    # 第3个请求应该被延迟（每秒最多2个）
    assert elapsed >= 0.5
