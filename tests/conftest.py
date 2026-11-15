import os
from pathlib import Path
from tempfile import TemporaryDirectory

# These tests clear the shelves and execute tasks. Give them their own data directory.
_data_dir = TemporaryDirectory(prefix="qinglong-tests-")
for key, directory in {
    "DB_PATH": "db",
    "PROJECT_PATH": "projects",
    "TASK_LOG_PATH": "logs",
    "UV_CACHE_DIR": "uv-cache",
}.items():
    os.environ[key] = str(Path(_data_dir.name) / directory)
