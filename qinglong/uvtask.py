import asyncio
import os
from pathlib import Path
from datetime import datetime
import logging

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
        self.proc = None
        self.log_file = cfg.TASK_LOG_PATH / (self.name + ".log")
        _logger.info(f"uvtask log file: {self.log_file}")

    async def run(self, wait=True):
        """运行命令，并将 stdout 和 stderr 直接写入日志文件"""
        cmd = f"uv run {self.uv_args} {self.cmd}"

        # 确保日志目录存在

        # 检查日志文件是否过大，如果超过限制则轮转
        await self._rotate_log_if_needed()
        if self.project_path.is_dir():
            task_env = self.project_path
        elif self.project_path.is_file():
            task_env = self.project_path.parent
        _logger.info(f"uvtask command: {cmd}")

        env = os.environ.copy()
        # 移除虚拟环境相关变量
        env.pop("VIRTUAL_ENV", None)
        env.pop("PYTHONPATH", None)
        # 直接重定向 stdout 和 stderr 到日志文件
        with open(self.log_file, "a") as log_f:
            self.proc = await asyncio.create_subprocess_shell(
                cmd,
                cwd=task_env,
                stdout=log_f,
                stderr=log_f,  # 也可以单独重定向 stderr
                env=env,
            )
            if wait:
                return await self.proc.wait()

    async def _rotate_log_if_needed(self):
        """如果日志文件过大，则进行轮转（重命名旧日志）"""
        if self.log_file.exists():
            file_size = self.log_file.stat().st_size
            if file_size >= self.max_log_size:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                rotated_log = self.log_file.with_name(f"{self.log_file.name}.{timestamp}")
                self.log_file.rename(rotated_log)

    async def get_logs(self, limit: int = 1000) -> list[str]:
        """返回倒序的日志（读取文件最后 `limit` 行）"""
        if not self.log_file.exists():
            _logger.warning(f"Log file {self.log_file} does not exist.")
            return []

        # 使用反向读取文件的方式获取最后 N 行（高效方式）
        with open(self.log_file, "rb") as f:
            # 移动到文件末尾
            f.seek(0, 2)  # os.SEEK_END = 2
            file_size = f.tell()
            remaining_bytes = file_size
            lines = []
            chunk_size = 4096  # 每次读取 4KB

            while remaining_bytes > 0 and len(lines) < limit:
                # 计算本次读取的字节数
                read_size = min(chunk_size, remaining_bytes)
                f.seek(-read_size, 1)  # os.SEEK_CUR = 1
                chunk = f.read(read_size)
                remaining_bytes -= read_size
                f.seek(-read_size, 1)

                # 按行分割并过滤空行
                chunk_lines = chunk.decode("utf-8", errors="ignore").split("\n")
                lines.extend(reversed(chunk_lines))

            # 返回最后 `limit` 行（并反转顺序，使最新的在前）
            return list(reversed(lines))[-limit:]

    async def wait(self):
        """等待进程结束"""
        if self.proc:
            return await self.proc.wait()
        return None
