import subprocess
from unittest.mock import MagicMock, patch

import pytest

from qinglong import errors
from qinglong.uvtask import UvTask


@patch("qinglong.uvtask.subprocess.run")
def test_uvtask_python_upgrade_and_cache_prune_call_uv(mock_run):
    mock_run.return_value = MagicMock()
    UvTask.python_upgrade()
    UvTask.cache_prune()
    assert mock_run.call_count == 2


def test_uvtask_is_running_false_when_no_process():
    t = UvTask(name="n", cmd="x", project_path="/tmp")
    assert t.is_running is False


def test_uvtask_is_running_true_when_process_poll_none():
    t = UvTask(name="n", cmd="x", project_path="/tmp")
    proc = MagicMock()
    proc.poll.return_value = None
    t._process = proc
    assert t.is_running is True


def test_uvtask_kill_raises_when_not_running():
    t = UvTask(name="n", cmd="x", project_path="/tmp")
    with pytest.raises(errors.TaskNotRunningError):
        t.kill()


def test_uvtask_kill_terminate_success():
    t = UvTask(name="n", cmd="x", project_path="/tmp")
    proc = MagicMock()
    proc.wait.return_value = 0
    t._process = proc
    rc = t.kill()
    proc.terminate.assert_called_once()
    assert rc == 0
    assert t._process is None


def test_uvtask_kill_on_wait_timeout_falls_back_to_kill():
    t = UvTask(name="n", cmd="x", project_path="/tmp")
    proc = MagicMock()
    proc.wait.side_effect = [subprocess.TimeoutExpired("cmd", 5), 0]
    t._process = proc
    t.kill()
    proc.kill.assert_called_once()


def test_uvtask_kill_handles_generic_exception_from_wait():
    t = UvTask(name="n", cmd="x", project_path="/tmp")
    proc = MagicMock()
    proc.terminate.return_value = None
    proc.wait.side_effect = RuntimeError("boom")
    proc.poll.return_value = 1
    t._process = proc
    rc = t.kill()
    assert rc == 1
    assert t._process is None
