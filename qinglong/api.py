from datetime import datetime
import shutil
import logging
from pathlib import Path

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


def clone_project(url: str, name: str = None):
    project_name = name if name else url.split("/")[-1]

    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    project_path = cfg.PROJECT_PATH / project_name
    project_downloader = ProjectDownloder(url=url, projectpath=project_path)

    if project_name in project_db:
        project_info: ProjectInfo = project_db[project_name]
        project_info.url = url
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
    project_info: ProjectInfo = project_db.get(project_name)
    if not project_info:
        raise errors.ProjectNotFoundError(project_name)

    clone_project(
        url=project_info.url,
        name=project_info.name,
    )


def remove_project(project_name: str):
    project_info: ProjectInfo = project_db.get(project_name)
    if not project_info:
        raise errors.ProjectNotFoundError(project_name)

    # TODO: 这里需要删除定时任务,或者对存在定时任务的工程报错。

    base_path = cfg.PROJECT_PATH
    project_path = base_path / project_info.name
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
    project_info: ProjectInfo = project_db.get(project_name)
    project_path = Path(project_info.project_path)
    for config_file in project_path.glob("config.*"):
        return config_file
    return project_path / "config.yaml"


def set_task(name: str, project_name: str, cron: str, cmd: str):
    if project_name not in project_db:
        raise errors.ProjectNotFoundError(project_name)

    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    project_info: ProjectInfo = project_db[project_name]

    if name in task_db:
        task_info: TaskInfo = task_db[name]
        if task_info.project_name != project_name:
            raise errors.SetTaskError(name)

        task_info.cron = cron
        task_info.command = cmd
        task_info.upgrade_at = created_at
        scheduler.remove_job(name)
    else:
        task_info = TaskInfo(
            name=name,
            project_name=project_name,
            cron=cron,
            command=cmd,
            created_at=created_at,
            upgrade_at=created_at,
            status="started",
        )

    if name in task_dict:
        task = task_dict[name]
        task.cmd = cmd
        task.project_path = Path(project_info.project_path)
    else:
        task = UvTask(name=name, cmd=task_info.command, project_path=project_info.project_path)
        task_dict[name] = task

    scheduler.add_job(func=task.run, trigger=task_info.cron, job_id=name)

    task_db[name] = task_info


def remove_task(task_name: str):
    if task_name not in task_db:
        raise errors.TaskNotFoundError(task_name)

    scheduler.remove_job(task_name)

    del task_dict[task_name]
    del task_db[task_name]


def start_task(task_name: str):
    if task_name not in task_db:
        raise errors.TaskNotFoundError(task_name)
    task_info: TaskInfo = task_db[task_name]
    task_info.status = TaskStatus.STARTED
    scheduler.resume_job(task_name)
    task_info.upgrade_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    task_db[task_name] = task_info
    return task_info


def pause_task(task_name: str):
    if task_name not in task_db:
        raise errors.TaskNotFoundError(task_name)
    task_info: TaskInfo = task_db[task_name]
    task_info.status = TaskStatus.PAUSED
    scheduler.pause_job(task_name)
    task_info.upgrade_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    task_db[task_name] = task_info
    return task_info


def run_task(task_name: str):
    if task_name not in task_db:
        raise errors.TaskNotFoundError(task_name)
    task_info: TaskInfo = task_db[task_name]

    scheduler.run_job(task_name, paused=(task_info.status == TaskStatus.PAUSED))

    return task_info


def kill_task(task_name: str):
    if task_name not in task_db:
        raise errors.TaskNotFoundError(task_name)
    task: UvTask = task_dict.get(task_name)
    if not task.is_running:
        raise errors.TaskNotRunningError(task_name)
    task.kill()


def get_task_logs(task_name: str, limit: int = 1000):
    if task_name not in task_db:
        raise errors.TaskNotFoundError(task_name)
    task: UvTask = task_dict.get(task_name)
    return task.get_logs(limit=limit)


def sync_project():
    for task_name, task_info in task_db.items():
        project_name = task_info.project_name
        if project_name not in project_db:
            del task_db[task_name]


def init_task():
    UvTask.cache_prune()
    for task_name, task_info in task_db.items():
        if task_info.project_name not in project_db:
            continue
        project_info: ProjectInfo = project_db[task_info.project_name]
        task = UvTask(name=task_name, cmd=task_info.command, project_path=project_info.project_path)
        task_dict[task_name] = task
        scheduler.add_job(
            func=task.run, trigger=task_info.cron, job_id=task_name, paused=(task_info.status == TaskStatus.PAUSED)
        )


def sync_task():
    tasks = set(task_db.keys())
    jobs = set(job.id for job in scheduler.jobs)
    for task_name in tasks - jobs:
        del task_db[task_name]
    for job_name in jobs - tasks:
        scheduler.remove_job(job_name)
