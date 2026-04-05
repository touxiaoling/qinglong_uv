import sys
import uuid
from unittest.mock import patch

from loguru import logger

from qinglong.my_logger import MultiThreadSubprocessManager, ThreadSubprocessLogger


def test_thread_subprocess_logger_run_command_success(tmp_path):
    name = f"t_{uuid.uuid4().hex[:8]}"
    with patch.object(logger, "add"):
        tlog = ThreadSubprocessLogger(name, str(tmp_path))
    r = tlog.run_command([sys.executable, "-c", "print('ok')"])
    assert r["success"] is True
    assert r["return_code"] == 0
    assert "ok" in (r.get("stdout") or "")


def test_thread_subprocess_logger_run_command_subprocess_error(tmp_path):
    name = f"t_{uuid.uuid4().hex[:8]}"
    with patch.object(logger, "add"):
        tlog = ThreadSubprocessLogger(name, str(tmp_path))
    with patch("qinglong.my_logger.subprocess.run", side_effect=OSError("boom")):
        r = tlog.run_command([sys.executable, "-c", "print(1)"])
    assert r["success"] is False


def test_thread_subprocess_logger_run_command_failure(tmp_path):
    name = f"t_{uuid.uuid4().hex[:8]}"
    with patch.object(logger, "add"):
        tlog = ThreadSubprocessLogger(name, str(tmp_path))
    r = tlog.run_command([sys.executable, "-c", "raise SystemExit(2)"])
    assert r["success"] is False
    assert r["return_code"] == 2


def test_thread_subprocess_logger_timeout(tmp_path):
    name = f"t_{uuid.uuid4().hex[:8]}"
    with patch.object(logger, "add"):
        tlog = ThreadSubprocessLogger(name, str(tmp_path))
    r = tlog.run_command([sys.executable, "-c", "import time; time.sleep(5)"], timeout=1)
    assert r["success"] is False


def test_thread_subprocess_logger_run_command_realtime(tmp_path):
    name = f"t_{uuid.uuid4().hex[:8]}"
    with patch.object(logger, "add"):
        tlog = ThreadSubprocessLogger(name, str(tmp_path))
    r = tlog.run_command_realtime([sys.executable, "-c", "print('rt')"])
    assert r["success"] is True
    assert any("rt" in line for line in r.get("stdout_lines", []))


def test_multi_thread_manager_routes_commands(tmp_path):
    with patch.object(logger, "add"):
        mgr = MultiThreadSubprocessManager(str(tmp_path))
        r = mgr.run_command_in_thread("w1", [sys.executable, "-c", "print(1)"])
    assert r["success"] is True
    assert mgr.get_thread_results("w1")
    assert "w1" in mgr.get_all_results()
