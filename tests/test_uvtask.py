import os
import pytest
import tempfile
from pathlib import Path
from qinglong.uvtask import UvTask
from qinglong.config import settings as cfg


@pytest.fixture
def temp_project_path(tmp_path: Path):
    """创建一个临时项目目录，测试完成后自动清理"""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    yield project_dir


@pytest.fixture
def uvtask(temp_project_path):
    """创建一个 UvTask 实例"""
    return UvTask(name="test_task", cmd="echo 'Hello, World!'", project_path=str(temp_project_path), uv_args="--python 3.13")


def test_uvtask_initialization(uvtask: UvTask, temp_project_path: Path):
    """测试 UvTask 初始化"""
    assert uvtask.name == "test_task"
    assert uvtask.cmd == "echo 'Hello, World!'"
    assert uvtask.project_path == Path(temp_project_path)
    assert uvtask.uv_args == "--python 3.13"
    assert uvtask.max_log_size == 10 * 1024 * 1024


def test_uvtask_run(uvtask: UvTask):
    """测试命令运行和日志记录"""
    uvtask.run()
    logs = list(uvtask.get_logs())
    for log in logs:
        assert "Hello, World!" in log
        break


def test_uvtask_with_file_project_path(tmp_path: Path):
    """测试使用文件路径作为项目路径"""
    test_file = tmp_path / "test.py"
    test_file.write_text("print('test')")

    task = UvTask(name="file_task", cmd="python test.py", project_path=str(test_file))
    task.run()
    for log in task.get_logs():
        assert "test" in log
        break
