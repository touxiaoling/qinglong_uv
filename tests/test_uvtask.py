import shlex
import sys
import time
from pathlib import Path

import pytest

from qinglong.uvtask import UvTask
from qinglong.config import settings as cfg


PYTHON_ARGS = f"--python {shlex.quote(sys._base_executable)}"


@pytest.fixture
def temp_project_path(tmp_path: Path):
    """创建一个临时项目目录，测试完成后自动清理"""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    project_dir.joinpath("pyproject.toml").write_text(
        """
        [project]
        name = "test-try"
        version = "0.1.0"
        description = "Add your description here"
        readme = "README.md"
        requires-python = ">=3.13"
        dependencies = []
        """
    )
    project_dir.joinpath("main.py").write_text("print('Hello, World!')")
    yield project_dir


@pytest.fixture
def uvtask(temp_project_path):
    """创建一个 UvTask 实例"""
    return UvTask(name="test_task", cmd="main.py", project_path=str(temp_project_path), uv_args=PYTHON_ARGS)


def test_uvtask_initialization(uvtask: UvTask, temp_project_path: Path):
    """测试 UvTask 初始化"""
    assert uvtask.name == "test_task"
    assert uvtask.cmd == "main.py"
    assert uvtask.project_path == Path(temp_project_path)
    assert uvtask.uv_args == PYTHON_ARGS
    assert uvtask.log_file.max_size == cfg.TASK_LOG_MAX_BYTES
    assert uvtask.log_file.backup_count == cfg.TASK_LOG_BACKUP_COUNT
    assert uvtask.timeout == 0


def test_uvtask_run(uvtask: UvTask):
    """测试命令运行和日志记录"""
    assert uvtask.run() == 0
    assert any("Hello, World!" in line for line in uvtask.get_logs())


def test_uvtask_with_file_project_path(tmp_path: Path):
    """测试使用文件路径作为项目路径"""
    test_file = tmp_path / "test.py"
    test_file.write_text("print('file project ran')")

    task = UvTask(name="file_task", cmd="python test.py", project_path=str(test_file), uv_args=PYTHON_ARGS)
    assert task.run() == 0
    assert any("file project ran" in line for line in task.get_logs())


def test_script_checkout_ignores_parent_project(tmp_path: Path):
    (tmp_path / "pyproject.toml").write_text("[invalid\n")
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    (checkout / "main.py").write_text("print('standalone script ran')")

    task = UvTask(name="standalone", cmd="main.py", project_path=str(checkout), uv_args=PYTHON_ARGS)

    assert task.run() == 0
    assert any("standalone script ran" in line for line in task.get_logs())


def test_uvtask_timeout_without_output(temp_project_path: Path):
    task = UvTask(
        name="timeout_task",
        cmd='python -c "import time; time.sleep(10)"',
        project_path=str(temp_project_path),
        uv_args=PYTHON_ARGS,
        timeout=1,
    )
    start = time.monotonic()
    task.run()
    elapsed = time.monotonic() - start
    assert elapsed < 3
    assert not task.is_running
    assert any("Timed out after 1s" in line for line in task.get_logs())
