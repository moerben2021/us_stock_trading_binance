import pytest
import os
from datetime import datetime
from utils.logger import setup_logger

def test_setup_logger_creates_log_file(tmp_path):
    """测试日志文件创建"""
    log_file = tmp_path / "test.log"
    logger = setup_logger("test_logger", str(log_file), "INFO")

    logger.info("Test message")

    assert log_file.exists()
    content = log_file.read_text()
    assert "Test message" in content

def test_logger_levels(tmp_path):
    """测试日志级别"""
    log_file = tmp_path / "test.log"
    logger = setup_logger("test_logger2", str(log_file), "WARNING")

    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")

    content = log_file.read_text()
    assert "Debug message" not in content
    assert "Info message" not in content
    assert "Warning message" in content
    assert "Error message" in content
