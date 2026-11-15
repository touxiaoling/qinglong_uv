import shelvez as shelve
from .config import settings as cfg
from .models import ProjectInfo, TaskInfo

_project_serializer = shelve.serializer.PydanticSerializer(ProjectInfo)  # type: ignore[arg-type]
_task_serializer = shelve.serializer.PydanticSerializer(TaskInfo)  # type: ignore[arg-type]

cfg.DB_PATH.mkdir(parents=True, exist_ok=True)
project_db = shelve.open(cfg.DB_PATH / "project.sqlite", serializer=_project_serializer)
task_db = shelve.open(cfg.DB_PATH / "task.sqlite", serializer=_task_serializer)
