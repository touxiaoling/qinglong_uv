from __future__ import annotations

import enum
from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class ProjectInfo(BaseModel):
    name: str
    url: str | None = None
    project_path: str
    created_at: str
    upgrade_at: str
    info: str | None = None


class TaskStatus(str, enum.Enum):
    STARTED = "started"
    PAUSED = "paused"


class TaskInfo(BaseModel):
    """
    任务信息
    """

    name: str
    project_name: str
    cron: str
    command: str
    status: TaskStatus = TaskStatus.PAUSED
    created_at: str
    upgrade_at: str
    info: str | None = None
    timeout: int = 0
    history_id: str | None = None
    notify_on_failure: bool = False


RunSource = Literal["scheduled", "manual"]
RunStatus = Literal["running", "succeeded", "failed", "timed_out", "stopped", "skipped", "interrupted"]


class RunInfo(BaseModel):
    id: int
    source: RunSource
    status: RunStatus
    scheduled_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    exit_code: int | None
    reason: str | None
    commit: str | None


class RunDetail(RunInfo):
    output: str | None


if __name__ == "__main__":
    task = ProjectInfo.model_validate(
        {
            "id": "123",
            "name": "test",
            "script": True,
            "url": "https://example.com",
            "upgrade": False,
            "project_path": "/path/to/project",
        }
    )
    print(task)
