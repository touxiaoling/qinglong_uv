import shelvez as shelve
from .config import settings as cfg
from .data_struct import ProjectInfo, TaskInfo

_project_serializer = shelve.serialer.PydanticSerializer(ProjectInfo)
_task_serializer = shelve.serialer.PydanticSerializer(TaskInfo)

project_db = shelve.open(cfg.DB_PATH / "project.sqlite", serializer=_project_serializer)
task_db = shelve.open(cfg.DB_PATH / "task.sqlite", serializer=_task_serializer)
