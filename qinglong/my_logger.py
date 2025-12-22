"""
多线程subprocess日志管理器
支持不同线程输出到不同日志文件
"""

import subprocess
import threading
import queue
import time
from pathlib import Path
from typing import List, Optional, Dict, Any
from loguru import logger
from datetime import datetime


class ThreadSubprocessLogger:
    """线程subprocess日志管理器"""

    def __init__(self, thread_name: str, log_dir: str = "logs"):
        self.thread_name = thread_name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

        # 创建线程特定的日志文件
        self.log_file = self.log_dir / f"{thread_name}_subprocess.log"

        # 绑定线程上下文到logger
        self.bound_logger = logger.bind(thread_name=thread_name)

        # 添加线程特定的日志处理器
        logger.add(
            self.log_file,
            rotation="1 day",
            retention="7 days",
            level="DEBUG",
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {extra[thread_name]} | {message}",
            encoding="utf-8",
            filter=lambda record: record["extra"].get("thread_name") == thread_name,
        )

        self.bound_logger.info(f"线程 {thread_name} 的subprocess日志器初始化完成")

    def run_command(self, command: List[str], timeout: Optional[int] = None) -> Dict[str, Any]:
        """执行命令并记录日志"""
        self.bound_logger.info(f"开始执行命令: {' '.join(command)}")

        start_time = time.time()
        result = {
            "command": command,
            "start_time": start_time,
            "success": False,
            "return_code": None,
            "stdout": "",
            "stderr": "",
            "duration": 0,
        }

        try:
            # 执行subprocess
            process = subprocess.run(command, capture_output=True, text=True, timeout=timeout, encoding="utf-8")

            # 记录结果
            result.update(
                {
                    "success": process.returncode == 0,
                    "return_code": process.returncode,
                    "stdout": process.stdout,
                    "stderr": process.stderr,
                    "duration": time.time() - start_time,
                }
            )

            # 记录输出
            if process.stdout:
                self.bound_logger.info(f"命令输出:\n{process.stdout}")

            if process.stderr:
                self.bound_logger.warning(f"命令错误输出:\n{process.stderr}")

            if process.returncode == 0:
                self.bound_logger.info(f"命令执行成功，耗时: {result['duration']:.2f}秒")
            else:
                self.bound_logger.error(f"命令执行失败，返回码: {process.returncode}")

        except subprocess.TimeoutExpired:
            result["success"] = False
            result["duration"] = time.time() - start_time
            self.bound_logger.error(f"命令执行超时 ({timeout}秒)")

        except Exception as e:
            result["success"] = False
            result["duration"] = time.time() - start_time
            self.bound_logger.error(f"命令执行异常: {e}")

        return result

    def run_command_realtime(self, command: List[str], timeout: Optional[int] = None) -> Dict[str, Any]:
        """实时执行命令并记录日志"""
        self.bound_logger.info(f"开始实时执行命令: {' '.join(command)}")

        start_time = time.time()
        result = {
            "command": command,
            "start_time": start_time,
            "success": False,
            "return_code": None,
            "stdout_lines": [],
            "stderr_lines": [],
            "duration": 0,
        }

        try:
            # 启动subprocess
            process = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1, universal_newlines=True
            )

            # 创建输出队列
            output_queue = queue.Queue()

            # 启动输出读取线程
            stdout_thread = threading.Thread(target=self._read_stream, args=(process.stdout, output_queue, "STDOUT"))
            stderr_thread = threading.Thread(target=self._read_stream, args=(process.stderr, output_queue, "STDERR"))

            stdout_thread.start()
            stderr_thread.start()

            # 处理输出
            while process.poll() is None or not output_queue.empty():
                try:
                    output_type, line = output_queue.get(timeout=0.1)
                    if line.strip():
                        if output_type == "STDOUT":
                            result["stdout_lines"].append(line.strip())
                            self.bound_logger.info(f"[OUT] {line.strip()}")
                        else:
                            result["stderr_lines"].append(line.strip())
                            self.bound_logger.warning(f"[ERR] {line.strip()}")
                except queue.Empty:
                    continue

            # 等待线程结束
            stdout_thread.join()
            stderr_thread.join()

            # 记录最终状态
            return_code = process.returncode
            result.update({"success": return_code == 0, "return_code": return_code, "duration": time.time() - start_time})

            if return_code == 0:
                self.bound_logger.info(f"实时命令执行成功，耗时: {result['duration']:.2f}秒")
            else:
                self.bound_logger.error(f"实时命令执行失败，返回码: {return_code}")

        except Exception as e:
            result["success"] = False
            result["duration"] = time.time() - start_time
            self.bound_logger.error(f"实时命令执行异常: {e}")

        return result

    def _read_stream(self, stream, output_queue, stream_type):
        """读取流数据"""
        try:
            for line in iter(stream.readline, ""):
                output_queue.put((stream_type, line))
        except Exception as e:
            self.bound_logger.error(f"读取{stream_type}流时发生错误: {e}")
        finally:
            stream.close()


class MultiThreadSubprocessManager:
    """多线程subprocess管理器"""

    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.loggers: Dict[str, ThreadSubprocessLogger] = {}
        self.results: Dict[str, List[Dict[str, Any]]] = {}

    def get_logger(self, thread_name: str) -> ThreadSubprocessLogger:
        """获取或创建线程日志器"""
        if thread_name not in self.loggers:
            self.loggers[thread_name] = ThreadSubprocessLogger(thread_name, str(self.log_dir))
            self.results[thread_name] = []
        return self.loggers[thread_name]

    def run_command_in_thread(
        self, thread_name: str, command: List[str], timeout: Optional[int] = None, realtime: bool = False
    ) -> Dict[str, Any]:
        """在指定线程中运行命令"""
        logger = self.get_logger(thread_name)

        if realtime:
            result = logger.run_command_realtime(command, timeout)
        else:
            result = logger.run_command(command, timeout)

        self.results[thread_name].append(result)
        return result

    def get_thread_results(self, thread_name: str) -> List[Dict[str, Any]]:
        """获取线程执行结果"""
        return self.results.get(thread_name, [])

    def get_all_results(self) -> Dict[str, List[Dict[str, Any]]]:
        """获取所有线程的执行结果"""
        return self.results.copy()


# 使用示例
def example_usage():
    """使用示例"""
    manager = MultiThreadSubprocessManager()

    def worker_thread(thread_id: int):
        """工作线程"""
        thread_name = f"worker_{thread_id}"

        # 模拟不同的命令
        commands = [
            ["echo", f"Hello from thread {thread_id}"],
            ["python", "-c", f"import time; [print(f'Thread {thread_id}: {i}') or time.sleep(0.5) for i in range(3)]"],
            ["ls", "-la"] if thread_id % 2 == 0 else ["pwd"],
        ]

        for cmd in commands:
            # 使用实时模式执行长时间命令
            realtime = len(cmd) > 2 and "python" in cmd[0]
            manager.run_command_in_thread(thread_name, cmd, realtime=realtime)
            time.sleep(1)

    # 启动多个线程
    threads = []
    for i in range(3):
        thread = threading.Thread(target=worker_thread, args=(i,))
        threads.append(thread)
        thread.start()

    # 等待所有线程完成
    for thread in threads:
        thread.join()

    # 输出结果摘要
    print("\n=== 执行结果摘要 ===")
    for thread_name, results in manager.get_all_results().items():
        print(f"\n{thread_name}:")
        for i, result in enumerate(results):
            status = "成功" if result["success"] else "失败"
            print(f"  命令 {i + 1}: {status} (耗时: {result['duration']:.2f}秒)")


if __name__ == "__main__":
    example_usage()
