from pathlib import Path
from datetime import datetime


class RotatingLogFile:
    def __init__(self, filename, max_size=1024 * 1024, backup_count=5, encoding="utf-8", mode="a"):
        """
        初始化日志文件类

        参数:
            filename (str): 日志文件名
            max_size (int): 单个日志文件最大大小（字节），默认为1MB
            backup_count (int): 保留的备份文件数量，默认为5
            encoding (str): 文件编码，默认为utf-8
            mode (str): 文件打开模式，默认为追加模式'a'
        """
        self.filename = Path(filename)
        self.max_size = max_size
        self.backup_count = backup_count
        self.encoding = encoding
        self.mode = mode

        # 确保日志目录存在
        self.filename.parent.mkdir(exist_ok=True)
        # 打开日志文件
        self._file = None

    def _should_rotate(self):
        """检查是否需要轮转日志"""
        try:
            return self.filename.stat().st_size >= self.max_size
        except OSError:
            return False

    def _open_file(self):
        """打开日志文件"""
        return open(self.filename, self.mode, encoding=self.encoding)

    def _backup_file(self, backup_count):
        if backup_count == 0:
            return self.filename
        return self.filename.with_name(f"{self.filename.stem}.{backup_count}{self.filename.suffix}")

    def _rotate(self):
        """执行日志轮转"""
        if self._file is not None:
            self.close()  # 关闭当前文件
            self._file = None

        # 重命名现有的备份文件（从旧到新）
        for i in range(self.backup_count - 1, 0, -1):
            src = self._backup_file(i)
            dst = self._backup_file(i + 1)
            if src.exists():
                src.replace(dst)

        # 重命名当前日志文件为.1
        first_backup = self._backup_file(1)
        self.filename.replace(first_backup)

        # 重新打开日志文件
        self._file = self._open_file()

    def write(self, message):
        """
        写入日志消息

        参数:
            message (str): 日志消息
        """
        if self._should_rotate():
            self.close()
            self._rotate()
            self._file = self._open_file()
        elif self._file is None or self._file.closed:
            self._file = self._open_file()

        self._file.write(message)

    def readlines(self, hint=1000):
        lines = []
        for i in range(self.backup_count + 1):
            backup_file = self._backup_file(i)
            if not backup_file.exists():
                break
            lines.extend(reversed(backup_file.read_text(encoding=self.encoding).splitlines()))
            if len(lines) >= hint:
                break

        return lines[:hint]

    def flush(self):
        """刷新文件缓冲区"""
        self._file.flush()

    def log(self, message, level="INFO"):
        """
        写入带格式的日志消息

        参数:
            message (str): 日志消息
            level (str): 日志级别
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if timestamp in message:
            log_entry = f"{message}\n"
        else:
            log_entry = f"[{timestamp}]: {message}\n"
        self.write(log_entry)

    def close(self):
        """关闭日志文件"""
        if self._file and not self._file.closed:
            self.flush()
            self._file.close()

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """上下文管理器退出"""
        self.close()


# 使用示例
if __name__ == "__main__":
    # 创建日志文件，限制大小为1KB，保留3个备份
    with RotatingLogFile("app.log", max_size=1024, backup_count=3) as log:
        # 测试日志轮转
        for i in range(1000):
            log.write(f"Test message {i}")

        # print(log.readlines(1000))
