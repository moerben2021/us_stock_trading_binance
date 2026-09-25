"""重试机制装饰器"""
import time
import logging
from functools import wraps
from dataclasses import dataclass
from typing import Callable, Any

logger = logging.getLogger(__name__)

@dataclass
class RetryConfig:
    """重试配置"""
    max_attempts: int
    interval_seconds: float
    backoff: str  # "fixed" 或 "exponential"

def retry_with_config(config: RetryConfig) -> Callable:
    """
    重试装饰器

    Args:
        config: 重试配置

    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # 边界检查：max_attempts 必须至少为 1
            if config.max_attempts < 1:
                raise ValueError(f"max_attempts 必须至少为 1，当前值为 {config.max_attempts}")

            last_exception = None

            for attempt in range(1, config.max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    if attempt < config.max_attempts:
                        # 计算等待时间
                        if config.backoff == "exponential":
                            wait_time = config.interval_seconds * (2 ** (attempt - 1))
                        else:
                            wait_time = config.interval_seconds

                        logger.warning(
                            f"{func.__name__} 失败 (尝试 {attempt}/{config.max_attempts}): {e}. "
                            f"等待 {wait_time}秒后重试..."
                        )
                        time.sleep(wait_time)
                    else:
                        logger.error(
                            f"{func.__name__} 在 {config.max_attempts} 次尝试后仍然失败: {e}"
                        )

            # 所有重试都失败，抛出最后一个异常
            raise last_exception

        return wrapper
    return decorator
