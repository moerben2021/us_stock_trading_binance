"""日志配置工具"""
import logging
from logging.handlers import TimedRotatingFileHandler
import os

def setup_logger(name: str, log_file: str, level: str = "INFO") -> logging.Logger:
    """
    配置日志记录器

    Args:
        name: 日志记录器名称
        log_file: 日志文件路径
        level: 日志级别（DEBUG/INFO/WARNING/ERROR/CRITICAL）

    Returns:
        配置好的日志记录器
    """
    # 创建日志目录
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 创建日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # 避免重复添加 handler
    if logger.handlers:
        return logger

    # 创建按日期轮转的文件处理器
    file_handler = TimedRotatingFileHandler(
        log_file,
        when='midnight',
        interval=1,
        backupCount=0,  # 不自动删除旧日志
        encoding='utf-8'
    )
    file_handler.suffix = "%Y-%m-%d"

    # 创建控制台处理器
    console_handler = logging.StreamHandler()

    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # 添加处理器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
