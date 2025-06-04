import os
import pytest
from pathlib import Path
from qinglong.filelog import RotatingLogFile


@pytest.fixture
def temp_log_file(tmp_path: Path):
    """创建临时日志文件用于测试"""
    log_file = tmp_path / "test.log"
    return log_file


def test_basic_logging(temp_log_file: Path):
    """测试基本的日志写入功能"""
    with RotatingLogFile(temp_log_file, max_size=1024, backup_count=3) as log:
        test_message = "测试日志消息"
        log.write(test_message)
        log.flush()
        # 验证文件是否被创建
        assert temp_log_file.exists()

        # 验证内容是否正确写入
        content = temp_log_file.read_text(encoding="utf-8")
        assert test_message in content


def test_log_rotation(temp_log_file: Path):
    """测试日志轮转功能"""
    with RotatingLogFile(temp_log_file, max_size=100, backup_count=3) as log:
        # 写入足够多的内容触发轮转
        for i in range(100):
            log.write(f"测试消息 {i}" * 10)
        log.flush()

        # 验证是否创建了备份文件
        backup_files = list(temp_log_file.parent.glob("test.*.log"))
        assert len(backup_files) > 0

        # 验证备份文件数量不超过设定值
        assert len(backup_files) <= 3


def test_log_readlines(temp_log_file: Path):
    """测试日志读取功能"""
    with RotatingLogFile(temp_log_file, max_size=1024, backup_count=3) as log:
        # 写入一些测试消息
        test_messages = [f"测试消息 {i}" for i in range(5)]
        for msg in test_messages:
            log.write(msg)
        log.flush()
        # 读取并验证消息
        read_messages = list(log.readlines(10))
        assert len(read_messages) == 5
        for msg in test_messages:
            assert msg in read_messages


def test_context_manager(temp_log_file: Path):
    """测试上下文管理器功能"""
    log = RotatingLogFile(temp_log_file)
    with log:
        log.write("测试上下文管理器")

    # 验证文件是否正确关闭
    assert log._file is None or log._file.closed


def test_buffer_functionality(temp_log_file: Path):
    """测试缓冲区功能"""
    buffer_size = 5
    with RotatingLogFile(temp_log_file, buffer_lines=buffer_size) as log:
        # 写入超过缓冲区大小的消息
        for i in range(10):
            log.write(f"缓冲区测试消息 {i}")

        # 验证缓冲区大小是否正确
        assert len(log.buffer) == buffer_size

        # 验证最新的消息是否在缓冲区中
        latest_messages = list(log.readlines(buffer_size))
        assert len(latest_messages) == buffer_size
        assert "缓冲区测试消息 9" in latest_messages[0]


def test_log_with_timestamp(temp_log_file: Path):
    """测试带时间戳的日志记录"""
    with RotatingLogFile(temp_log_file) as log:
        test_message = "测试时间戳消息"
        log.log(test_message, level="INFO")
        log.flush()
        content = temp_log_file.read_text(encoding="utf-8")
        assert test_message in content
        assert "[" in content and "]" in content  # 验证时间戳格式


def test_file_encoding(temp_log_file: Path):
    """测试文件编码功能"""
    test_message = "测试中文编码"
    with RotatingLogFile(temp_log_file, encoding="utf-8") as log:
        log.write(test_message)
        log.flush()
    content = temp_log_file.read_text(encoding="utf-8")
    assert test_message in content
