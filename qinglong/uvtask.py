import functools
import os
import shlex
import signal
import subprocess
import threading
from datetime import datetime
from pathlib import Path

from . import errors, notify, runs
from .config import settings as cfg
from .download import git_revision
from .filelog import RotatingLogFile
from .models import RunSource, RunStatus

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
        *,
        history_id: str | None = None,
        project_name: str = "",
    ):
        self.name = name
        self.cmd = cmd
        self.uv_args = uv_args
        self.project_path = Path(project_path)
        self.max_log_size = cfg.TASK_LOG_MAX_BYTES if max_log_size is None else max_log_size
        self.timeout = timeout
        self.history_id = history_id
        self.project_name = project_name
        self.log_file = RotatingLogFile(
            cfg.TASK_LOG_PATH / (self.name + ".log"), max_size=self.max_log_size, backup_count=cfg.TASK_LOG_BACKUP_COUNT
        )
        self._lock = threading.Lock()
        self._stop_lock = threading.Lock()
        self._process: subprocess.Popen[str] | None = None
        self._finished: threading.Event | None = None
        self._enabled = True
        self._shutting_down = False
        self._stop_reason: tuple[RunStatus, str] | None = None

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
            self._shutting_down = stop_running
        if finished is not None:
            self._stop(finished, "interrupted", "Service shutdown")

    def record_skips(self, source: RunSource, times: list[datetime], reason: str):
        with self._lock:
            if self._enabled and self.history_id is not None:
                runs.skip_runs(self.history_id, source, times, reason)

    def run(
        self,
        *,
        command: str | None = None,
        timeout: int | None = None,
        scheduled_at: datetime | None = None,
        source: RunSource = "manual",
        notify_on_failure: bool = False,
    ):
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
                if self._shutting_down and self.history_id is not None and scheduled_at is not None:
                    runs.skip_runs(self.history_id, source, [scheduled_at], "Service shut down before the run started")
                return
            finished = self._finished = threading.Event()
            self._stop_reason = None

        timer = None
        run_id = None
        output = runs.RunOutput() if self.history_id is not None and scheduled_at is not None else None
        return_code = None
        reason = None

        def log(message: str):
            line = self.log_file.log(message)
            if output is not None:
                output.append(line)

        try:
            if timeout > 0:
                timer = threading.Timer(timeout, self._stop, args=(finished, "timed_out", f"Timed out after {timeout}s"))
                timer.start()
            if self.history_id is not None and scheduled_at is not None:
                _, commit = git_revision(task_path)
                run_id = runs.start_run(self.history_id, source, scheduled_at, commit)
            with self.log_file:
                try:
                    log("Run started")
                    if has_project:
                        return_code = self._prepare_project(task_path, log)
                        if return_code != 0:
                            return return_code
                    return_code = self._execute(cmd, task_path, log)
                    return return_code
                except Exception as exc:
                    reason = str(exc)
                    raise
                finally:
                    if timer is not None:
                        timer.cancel()
                        timer.join()
                    with self._stop_lock:
                        status: RunStatus = "succeeded" if return_code == 0 else "failed"
                        if self._stop_reason is not None:
                            status, reason = self._stop_reason
                        try:
                            log(f"{reason or 'Run finished'} (exit code {return_code})")
                        finally:
                            if self.history_id is not None and run_id is not None and output is not None:
                                runs.finish_run(self.history_id, run_id, status, return_code, reason, output.text())
                                if notify_on_failure:
                                    notify.enqueue(self.history_id, self.project_name, self.name, run_id, status)
        finally:
            if timer is not None:
                timer.cancel()
            with self._lock:
                self._finished = None
                finished.set()

    def _prepare_project(self, task_path, log):
        project_dir = task_path.resolve()
        lock = _project_locks.setdefault(project_dir, threading.Lock())
        while not lock.acquire(timeout=0.1):
            with self._lock:
                if self._stop_reason is not None:
                    return None
        try:
            if project_dir in _prepared_projects:
                return 0
            code = self._execute(["uv", "venv", "--clear", ".venv"], task_path, log)
            if code == 0:
                _prepared_projects.add(project_dir)
            return code
        finally:
            lock.release()

    def _execute(self, cmd, task_path, log):
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
                log(f"Could not start task: {exc}")
                raise
            self._process = process

        try:
            assert process.stdout is not None
            with process.stdout:
                for line in process.stdout:
                    log(line)
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
        return_code = self._stop(finished, "stopped", "Stopped manually")
        finished.wait(5)
        return return_code

    def _stop(self, finished: threading.Event, status: RunStatus, reason: str) -> int | None:
        with self._stop_lock:
            with self._lock:
                if self._finished is not finished or self._stop_reason is not None:
                    return None
                self._stop_reason = (status, reason)
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
