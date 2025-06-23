import os
from pathlib import Path
import logging
import subprocess
import threading
import functools

from .filelog import RotatingLogFile
from .config import settings as cfg
from . import errors

_logger = logging.getLogger(__name__)


@functools.cache
def _env():
    env = os.environ.copy()
    env.pop("VIRTUAL_ENV", None)
    env.pop("PYTHONPATH", None)
    env["PYTHONUNBUFFERED"] = "1"
    return env


class UvTask:
    _global_task_lock = threading.Lock()
    _project_inited = set()

    def __init__(
        self,
        name: str,
        cmd: str,
        project_path: str,
        uv_args: str = "",
        max_log_size: int = 10 * 1024 * 1024,  # 10MB
    ):
        self.name = name
        self.cmd = cmd
        self.uv_args = uv_args
        self.project_path = Path(project_path)
        self.max_log_size = max_log_size  # 日志文件最大大小（字节）
        self.log_file = RotatingLogFile(cfg.TASK_LOG_PATH / (self.name + ".log"))
        self._process = None  # 添加进程属性
        _logger.info(f"uvtask log file: {self.log_file}")

    @classmethod
    def cache_prune(cls):
        subprocess.run(["uv", "cache", "prune"], check=True, env=_env())

    @property
    def is_running(self) -> bool:
        """检查进程是否正在运行
        Returns:
            bool: 如果进程正在运行返回True，否则返回False
        """
        if self._process is None:
            return False
        return self._process.poll() is None

    @property
    def env(self):
        return _env()

    def init_project(self, project_path: Path):
        with self._global_task_lock:
            abs_path_str = str(project_path.absolute())
            if abs_path_str not in self._project_inited:
                subprocess.run(["uv", "venv"], cwd=project_path, env=self.env, check=True)
                _logger.info(f"uvtask project inited: {abs_path_str}")
                self._project_inited.add(abs_path_str)

    def run(self):
        """运行命令，并将 stdout 和 stderr 直接写入日志文件"""
        cmd = f"uv run {self.uv_args} {self.cmd}"
        cmd = [v for v in cmd.split(" ") if v]
        _logger.info(f"uvtask command: {cmd}")

        if self.project_path.is_dir():
            task_env = self.project_path
            self.init_project(self.project_path)
        elif self.project_path.is_file():
            task_env = self.project_path.parent

        # 直接重定向 stdout 和 stderr 到日志文件
        with self.log_file as log_f:
            self._process = subprocess.Popen(
                cmd,
                cwd=task_env,
                env=self.env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            try:
                while line := self._process.stdout.readline():
                    log_f.log(line)

                return_code = self._process.wait()
            finally:
                self._process = None
        _logger.info(f"uvtask command completed with exit code {return_code}: {cmd}")

    def kill(self):
        """终止正在运行的进程"""
        process = self._process
        if process is None:
            raise errors.TaskNotRunningError(self.name)

        try:
            process.terminate()
            process.wait(timeout=5)  # 等待进程终止
            _logger.info(f"Successfully terminated process for task: {self.name}")
        except subprocess.TimeoutExpired:
            process.kill()  # 如果进程没有及时终止，强制结束
            _logger.warning(f"Force killed process for task: {self.name}")
        except Exception as e:
            _logger.error(f"Error while killing process for task {self.name}: {e}")
        finally:
            self._process = None

    def get_logs(self, limit: int = 1000):
        return self.log_file.readlines(limit)
