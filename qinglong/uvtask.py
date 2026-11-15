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

_project_locks: dict[Path, threading.Lock] = {}
_prepared_projects: set[Path] = set()


@functools.cache
def _env():
    env = os.environ.copy()
    env.pop("VIRTUAL_ENV", None)
    env.pop("PYTHONPATH", None)
    env.pop("UV_PROJECT_ENVIRONMENT", None)
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
            return self._finished is not None

    @property
    def env(self):
        return _env()

    def disable(self, *, stop_running=False):
        with self._lock:
            finished = self._finished
            if finished is not None and not stop_running:
                raise errors.TaskRunningError(self.name)
            self._enabled = False
        if finished is not None:
            self._stop(finished, "Service shutdown")

    def run(self, *, command: str | None = None, timeout: int | None = None):
        command = self.cmd if command is None else command
        timeout = self.timeout if timeout is None else timeout
        task_path = self.project_path.parent if self.project_path.is_file() else self.project_path
        cmd = ["uv", "run"]
        has_project = (task_path / "pyproject.toml").is_file()
        if not has_project:
            # A script-only checkout can be nested inside the panel's own project.
            cmd.extend(["--no-project", "--isolated"])
        cmd.extend(shlex.split(self.uv_args))
        cmd.extend(shlex.split(command))
        with self._lock:
            if not self._enabled or self._finished is not None:
                return
            finished = self._finished = threading.Event()
            self._stop_reason = None

        timer = None
        if timeout > 0:
            timer = threading.Timer(timeout, self._stop, args=(finished, f"Timed out after {timeout}s"))
            timer.start()
        return_code = None
        try:
            with self.log_file as log_f:
                try:
                    log_f.log("Run started")
                    if has_project:
                        project_dir = task_path.resolve()
                        with _project_locks.setdefault(project_dir, threading.Lock()):
                            if project_dir not in _prepared_projects:
                                return_code = self._execute(["uv", "venv", "--clear", ".venv"], task_path, log_f)
                                if return_code != 0:
                                    return return_code
                                _prepared_projects.add(project_dir)
                    return_code = self._execute(cmd, task_path, log_f)
                    return return_code
                finally:
                    if timer is not None:
                        timer.cancel()
                        timer.join()
                    with self._stop_lock:
                        log_f.log(f"{self._stop_reason or 'Run finished'} (exit code {return_code})")
        finally:
            with self._lock:
                self._finished = None
                finished.set()

    def _execute(self, cmd, task_path, log_f):
        with self._lock:
            if self._stop_reason is not None:
                return None
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
                log_f.log(f"Could not start task: {exc}")
                raise
            self._process = process

        try:
            assert process.stdout is not None
            with process.stdout:
                for line in process.stdout:
                    log_f.log(line)
            return process.wait()
        finally:
            with self._stop_lock:
                if process.poll() is None:
                    self._terminate(process)
                with self._lock:
                    self._process = None

    def kill(self) -> int | None:
        with self._lock:
            finished = self._finished
        if finished is None:
            raise errors.TaskNotRunningError(self.name)
        return_code = self._stop(finished, "Stopped manually")
        finished.wait(5)
        return return_code

    def _stop(self, finished: threading.Event, reason: str) -> int | None:
        with self._stop_lock:
            with self._lock:
                if self._finished is not finished or self._stop_reason is not None:
                    return None
                self._stop_reason = reason
                process = self._process
            if process is not None:
                return self._terminate(process)
        return None

    @staticmethod
    def _terminate(process: subprocess.Popen[str]) -> int | None:
        try:
            if os.name == "posix":
                os.killpg(process.pid, signal.SIGTERM)
            else:
                process.terminate()
        except ProcessLookupError:
            return process.poll()
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
