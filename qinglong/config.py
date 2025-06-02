from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    配置文件
    """

    model_config = SettingsConfigDict(case_sensitive=True, env_ignore_empty=True)
    # 代理设置
    PROXY: str = ""
    DB_PATH: Path = Path("./data/db")
    # 任务脚本路径
    PROJECT_PATH: Path = Path("./data/projects")
    # 任务日志路径
    TASK_LOG_PATH: Path = Path("./data/log")
    # 任务日志最大大小
    TASK_LOG_MAX_BYTES: int = 1024 * 1024
    # 任务日志备份数量
    TASK_LOG_BACKUP_COUNT: int = 5
    DEBUG: bool = True

    DOWNLOAD_HEADERS: dict = {
        "Sec-Ch-Ua": '"Google Chrome";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"macOS"',
        "Sec-Fetch-Dest": "image",
        "Sec-Fetch-Mode": "no-cors",
        "Sec-Fetch-Site": "cross-site",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    }


settings = Settings()
