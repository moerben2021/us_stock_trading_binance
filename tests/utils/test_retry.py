import pytest
from utils.retry import retry_with_config, RetryConfig

def test_retry_succeeds_on_first_attempt():
    """测试首次成功不重试"""
    call_count = 0

    @retry_with_config(RetryConfig(max_attempts=3, interval_seconds=0.1, backoff="fixed"))
    def successful_func():
        nonlocal call_count
        call_count += 1
        return "success"

    result = successful_func()
    assert result == "success"
    assert call_count == 1

def test_retry_succeeds_after_failures():
    """测试失败后重试成功"""
    call_count = 0

    @retry_with_config(RetryConfig(max_attempts=3, interval_seconds=0.1, backoff="fixed"))
    def eventually_successful_func():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ValueError("Not yet")
        return "success"

    result = eventually_successful_func()
    assert result == "success"
    assert call_count == 3

def test_retry_fails_after_max_attempts():
    """测试达到最大重试次数后失败"""
    call_count = 0

    @retry_with_config(RetryConfig(max_attempts=3, interval_seconds=0.1, backoff="fixed"))
    def always_failing_func():
        nonlocal call_count
        call_count += 1
        raise ValueError("Always fails")

    with pytest.raises(ValueError, match="Always fails"):
        always_failing_func()

    assert call_count == 3
