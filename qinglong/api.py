from __future__ import annotations

from datetime import datetime
import shutil
import logging
import shlex
from pathlib import Path

from apscheduler.triggers.base import BaseTrigger

from .config import settings as cfg
from .models import ProjectInfo, TaskInfo, TaskStatus
from .database import project_db, task_db
from .scheduler import scheduler
from .download import ProjectDownloder
from .uvtask import UvTask
from . import errors

_logger = logging.getLogger(__name__)
task_dict: dict[str, UvTask] = {}


def list_projects():
    projects: list[dict] = [v.model_dump() for v in project_db.values()]
    return projects


def list_tasks():
    tasks: list[dict] = [v.model_dump() for v in task_db.values()]
    return tasks


def clone_project(url: str, name: str | None = None):
    project_name = name or url.rstrip("/").rsplit("/", 1)[-1]
    if project_name in {"", ".", ".."} or "/" in project_name or "\\" in project_name:
        raise ValueError("Use a project name without path separators.")

    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    project_path = cfg.PROJECT_PATH / project_name
    project_downloader = ProjectDownloder(url=url, projectpath=project_path)

    if project_name in project_db:
        project_info: ProjectInfo = project_db[project_name]
        if project_info.url != url:
            raise errors.ProjectConflictError(f"Project '{project_name}' already uses a different repository URL.")
        project_info.project_path = str(project_path)
        project_info.upgrade_at = created_at
    else:
        project_info = ProjectInfo(
            name=project_name,
            url=url,
            project_path=str(project_path),
            created_at=created_at,
            upgrade_at=created_at,
        )

    project_downloader.download()

    project_db[project_name] = project_info


def pull_project(project_name: str):
    project_info = project_db.get(project_name)
    if not project_info:
        raise errors.ProjectNotFoundError(project_name)
    if project_info.url is None:
        raise errors.ProjectNotFoundError(project_name)

    clone_project(
        url=project_info.url,
        name=project_info.name,
    )


def remove_project(project_name: str):
    project_info = project_db.get(project_name)
    if not project_info:
        raise errors.ProjectNotFoundError(project_name)

    if any(task.project_name == project_name for task in task_db.values()):
        raise errors.ProjectHasTasksError(project_name)

    project_path = Path(project_info.project_path)
    _logger.debug(f"remove project: {project_path},absolute: {project_path.absolute()}")
    if project_path.exists():
        if project_path.is_file():
            project_path.unlink()
        else:
            _logger.debug(f"remove project use shutil: {project_path}")
            shutil.rmtree(str(project_path.absolute()))
    else:
        _logger.debug(f"remove project not exist: {project_path}")
        raise errors.ProjectNotFoundError(project_name)

    del project_db[project_name]


def get_project_config(project_name: str):
    project_info = project_db.get(project_name)
    if not project_info:
        raise errors.ProjectNotFoundError(project_name)

    project_path = Path(project_info.project_path)
    if project_path.is_file():
        project_path = project_path.parent
    for config_file in sorted(project_path.glob("config.*")):
        if config_file.is_file() and config_file.suffix.lower() in {".toml", ".yaml", ".yml"}:
            return config_file
    return project_path / "config.yaml"


def set_task(name: str, project_name: str, cron: str, cmd: str, timeout: int = 0):
    project_info = project_db.get(project_name)
    if project_info is None:
        raise errors.ProjectNotFoundError(project_name)
    previous = task_db.get(name)
    if previous is None and (name in {"", ".", ".."} or "/" in name or "\\" in name):
        raise ValueError("Use a task name without path separators.")
    if not shlex.split(cmd):
        raise ValueError("Enter a command.")
    trigger = scheduler.parse_trigger(cron)

    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if previous is not None:
        if previous.project_name != project_name:
            raise errors.SetTaskError(name)
        task_info = previous.model_copy(update={"cron": cron, "command": cmd, "upgrade_at": created_at, "timeout": timeout})
    else:
        task_info = TaskInfo(
            name=name,
            project_name=project_name,
            cron=cron,
            command=cmd,
            created_at=created_at,
            upgrade_at=created_at,
            status=TaskStatus.STARTED,
            timeout=timeout,
        )

    task_db[name] = task_info
    try:
        job = scheduler.get_job(name) if previous is not None and previous.cron == cron else None
        if job is not None:
            job.modify(kwargs={"command": cmd, "timeout": timeout})
        else:
            _register_task(task_info, project_info, trigger)
    except Exception:
        if previous is None:
            del task_db[name]
        else:
            task_db[name] = previous
        raise
    return task_info


def _register_task(task_info: TaskInfo, project_info: ProjectInfo, trigger: BaseTrigger):
    name = task_info.name
    task = task_dict.get(name)
    if task is None:
        task = UvTask(name=name, cmd=task_info.command, project_path=project_info.project_path, timeout=task_info.timeout)

    scheduler.add_job(
        func=task.run,
        trigger=trigger,
        job_id=name,
        paused=task_info.status == TaskStatus.PAUSED,
        replace_existing=True,
        kwargs={"command": task_info.command, "timeout": task_info.timeout},
    )
    task_dict[name] = task


def remove_task(task_name: str):
    if task_name not in task_db:
        raise errors.TaskNotFoundError(task_name)

    task = task_dict.get(task_name)
    if task is not None:
        task.disable()
    if scheduler.get_job(task_name) is not None:
        scheduler.remove_job(task_name)

    task_dict.pop(task_name, None)
    del task_db[task_name]


def start_task(task_name: str):
    return _set_task_status(task_name, TaskStatus.STARTED)


def pause_task(task_name: str):
    return _set_task_status(task_name, TaskStatus.PAUSED)


def _set_task_status(task_name: str, status: TaskStatus):
    previous = task_db.get(task_name)
    if previous is None:
        raise errors.TaskNotFoundError(task_name)
    updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    task_info = previous.model_copy(update={"status": status, "upgrade_at": updated_at})
    task_db[task_name] = task_info
    try:
        if status == TaskStatus.PAUSED:
            scheduler.pause_job(task_name)
        else:
            scheduler.resume_job(task_name)
    except Exception:
        task_db[task_name] = previous
        raise
    return task_info


def run_task(task_name: str):
    if task_name not in task_db:
        raise errors.TaskNotFoundError(task_name)
    task_info: TaskInfo = task_db[task_name]

    scheduler.run_job(task_name)

    return task_info


def kill_task(task_name: str):
    if task_name not in task_db:
        raise errors.TaskNotFoundError(task_name)
    task = task_dict.get(task_name)
    if task is None or not task.is_running:
        raise errors.TaskNotRunningError(task_name)
    task.kill()


def get_task_logs(task_name: str, limit: int = 1000):
    if task_name not in task_db:
        raise errors.TaskNotFoundError(task_name)
    task = task_dict.get(task_name)
    if task is None:
        raise errors.TaskNotFoundError(task_name)
    return task.get_logs(limit=limit)


def sync_project():
    for task_name, task_info in task_db.items():
        project_name = task_info.project_name
        if project_name not in project_db:
            remove_task(task_name)


def init_task():
    sync_task()


def sync_task():
    tasks = set(task_db)
    jobs = {job.id for job in scheduler.jobs}
    for job_name in jobs - tasks:
        scheduler.remove_job(job_name)
    for task_name in tasks - jobs:
        task_info = task_db[task_name]
        project_info = project_db.get(task_info.project_name)
        if project_info is None:
            _logger.warning("Task %s has no project %s", task_name, task_info.project_name)
            continue
        try:
            if not shlex.split(task_info.command):
                raise ValueError("Enter a command.")
            trigger = scheduler.parse_trigger(task_info.cron)
            _register_task(task_info, project_info, trigger)
        except (ValueError, OSError) as exc:
            _logger.warning("Could not register task %s: %s", task_name, exc)
