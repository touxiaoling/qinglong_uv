import enum

from pydantic import BaseModel


class ProjectInfo(BaseModel):
    name: str
    one_file: bool = False
    url: str = None
    project_path: str
    created_at: str
    upgrade_at: str
    info: str = None


class TaskStatus(str, enum.Enum):
    STARTED: str = "started"
    PAUSED: str = "paused"


class TaskInfo(BaseModel):
    """
    任务信息
    """

    name: str
    project_name: str
    status: str
    cron: str
    command: str
    status: TaskStatus = TaskStatus.PAUSED
    created_at: str
    upgrade_at: str
    info: str = None


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
