import os
from pathlib import Path
import logging
import subprocess

from .filelog import RotatingLogFile
from .config import settings as cfg

_logger = logging.getLogger(__name__)


class UvTask:
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
        _logger.info(f"uvtask log file: {self.log_file}")

    def run(self):
        """运行命令，并将 stdout 和 stderr 直接写入日志文件"""
        cmd = f"uv run {self.uv_args} {self.cmd}"
        cmd = [v for v in cmd.split(" ") if v]
        _logger.info(f"uvtask command: {cmd}")

        if self.project_path.is_dir():
            task_env = self.project_path
        elif self.project_path.is_file():
            task_env = self.project_path.parent

        env = os.environ.copy()
        # 移除虚拟环境相关变量
        env.pop("VIRTUAL_ENV", None)
        env.pop("PYTHONPATH", None)
        env["PYTHONUNBUFFERED"] = "1"
        # 直接重定向 stdout 和 stderr 到日志文件
        with self.log_file as log_f:
            with subprocess.Popen(
                cmd,
                cwd=task_env,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            ) as proc:
                while line := proc.stdout.readline():
                    log_f.log(line.rstrip())

                return_code = proc.wait()
        _logger.info(f"uvtask command completed with exit code {return_code}: {cmd}")

    def get_logs(self, limit: int = 1000):
        return self.log_file.readlines(limit)
