import functools
import os
import shlex
import signal
import subprocess
import threading
from pathlib import Path

from . import errors
from .config import settings as cfg
from .filelog import RotatingLogFile


@functools.cache
def _env():
    env = os.environ.copy()
    env.pop("VIRTUAL_ENV", None)
    env.pop("PYTHONPATH", None)
    env["PYTHONUNBUFFERED"] = "1"
    return env


class UvTask:
    def __init__(
        self,
        name: str,
        cmd: str,
        project_path: str,
        uv_args: str = "",
        max_log_size: int | None = None,
        timeout: int = 0,
    ):
        self.name = name
        self.cmd = cmd
        self.uv_args = uv_args
        self.project_path = Path(project_path)
        self.max_log_size = cfg.TASK_LOG_MAX_BYTES if max_log_size is None else max_log_size
        self.timeout = timeout
        self.log_file = RotatingLogFile(
            cfg.TASK_LOG_PATH / (self.name + ".log"), max_size=self.max_log_size, backup_count=cfg.TASK_LOG_BACKUP_COUNT
        )
        self._lock = threading.Lock()
        self._stop_lock = threading.Lock()
        self._process: subprocess.Popen[str] | None = None
        self._finished: threading.Event | None = None
        self._enabled = True
        self._stop_reason: str | None = None

    @property
    def is_running(self) -> bool:
        with self._lock:
            return self._process is not None

    @property
    def env(self):
        return _env()

    def disable(self, *, stop_running=False):
        with self._lock:
            process = self._process
            if process is not None and not stop_running:
                raise errors.TaskRunningError(self.name)
            self._enabled = False
        if process is not None:
            self._stop(process, "Service shutdown")

    def run(self, *, command: str | None = None, timeout: int | None = None):
        command = self.cmd if command is None else command
        timeout = self.timeout if timeout is None else timeout
        task_path = self.project_path.parent if self.project_path.is_file() else self.project_path
        cmd = ["uv", "run"]
        if not (task_path / "pyproject.toml").is_file():
            # A script-only checkout can be nested inside the panel's own project.
            cmd.extend(["--no-project", "--isolated"])
        cmd.extend(shlex.split(self.uv_args))
        cmd.extend(shlex.split(command))
        with self._lock:
            if not self._enabled or self._process is not None:
                return
            try:
                process = subprocess.Popen(
                    cmd,
                    cwd=task_path,
                    env=self.env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    encoding="utf-8",
                    errors="replace",
                    start_new_session=os.name == "posix",
                )
            except OSError as exc:
                with self.log_file as log_f:
                    log_f.log(f"Could not start task: {exc}")
                raise
            self._process = process
            finished = self._finished = threading.Event()
            self._stop_reason = None

        timer = None
        if timeout > 0:
            timer = threading.Timer(timeout, self._stop, args=(process, f"Timed out after {timeout}s"))
            timer.start()
        try:
            with self.log_file as log_f:
                try:
                    assert process.stdout is not None
                    with process.stdout:
                        log_f.log("Run started")
                        for line in process.stdout:
                            log_f.log(line)
                    return_code = process.wait()
                finally:
                    if timer is not None:
                        timer.cancel()
                        timer.join()
                    if process.poll() is None:
                        self._stop(process, "Log capture failed")
                    with self._stop_lock:
                        log_f.log(f"{self._stop_reason or 'Run finished'} (exit code {process.returncode})")
        finally:
            with self._stop_lock, self._lock:
                self._process = None
                self._finished = None
                finished.set()
        return return_code

    def kill(self) -> int | None:
        with self._lock:
            process = self._process
            finished = self._finished
        if process is None or finished is None:
            raise errors.TaskNotRunningError(self.name)
        return_code = self._stop(process, "Stopped manually")
        finished.wait(5)
        return return_code

    def _stop(self, process: subprocess.Popen[str], reason: str) -> int | None:
        with self._stop_lock:
            if self._process is not process or self._stop_reason is not None:
                return process.returncode
            try:
                if os.name == "posix":
                    os.killpg(process.pid, signal.SIGTERM)
                else:
                    process.terminate()
            except ProcessLookupError:
                return process.poll()
            self._stop_reason = reason
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                pass
            # uv can exit before a descendant that still holds the output pipe open.
            try:
                if os.name == "posix":
                    os.killpg(process.pid, signal.SIGKILL)
                elif process.poll() is None:
                    process.kill()
            except ProcessLookupError:
                pass
            return process.wait()

    def get_logs(self, limit: int = 1000):
        return self.log_file.readlines(limit)
