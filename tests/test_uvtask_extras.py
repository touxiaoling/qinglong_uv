import os
import signal
import subprocess
from threading import Event
from unittest.mock import MagicMock, call

import pytest

from qinglong import errors
from qinglong.uvtask import UvTask


def test_uvtask_is_running_false_when_no_process():
    t = UvTask(name="n", cmd="x", project_path="/tmp")
    assert t.is_running is False


def test_uvtask_is_running_between_subprocesses():
    t = UvTask(name="n", cmd="x", project_path="/tmp")
    t._finished = Event()
    assert t.is_running is True


def test_uvtask_kill_raises_when_not_running():
    t = UvTask(name="n", cmd="x", project_path="/tmp")
    with pytest.raises(errors.TaskNotRunningError):
        t.kill()


@pytest.mark.skipif(os.name != "posix", reason="POSIX process groups")
def test_uvtask_kill_on_wait_timeout_falls_back_to_group_kill(monkeypatch):
    t = UvTask(name="n", cmd="x", project_path="/tmp")
    killpg = MagicMock()
    monkeypatch.setattr(os, "killpg", killpg)
    proc = MagicMock()
    proc.pid = 1234
    proc.wait.side_effect = [subprocess.TimeoutExpired("cmd", 5), -signal.SIGKILL]
    assert t._terminate(proc) == -signal.SIGKILL
    assert killpg.call_args_list == [call(1234, signal.SIGTERM), call(1234, signal.SIGKILL)]
