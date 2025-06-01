from datetime import datetime
import shutil
import logging

from .config import settings as cfg
from .data_struct import ProjectInfo, TaskInfo, TaskStatus
from .data_base import project_db, task_db
from .scheduler import scheduler
from .download import FileDownloader, ProjectDownloder
from .uvtask import UvTask
from . import errors

_logger = logging.getLogger(__name__)


def list_projects():
    projects: list[dict] = [v.model_dump() for v in project_db.values()]
    return projects


def list_tasks():
    tasks: list[dict] = [v.model_dump() for v in task_db.values()]
    return tasks


def upload_script(
    name: str,
    contents: bytes,
):
    script_path = cfg.SCRIPT_PATH / name
    script_path.write_bytes(contents)
    script_path = script_path.absolute()
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    project_db[script_path] = ProjectInfo(
        name=name,
        one_file=True,
        url=None,
        project_path=str(script_path),
        created_at=created_at,
        upgrade_at=created_at,
    )


def pull_project(url: str, name: str = None, one_file: bool = False):
    project_name = name if name else url.split("/")[-1]

    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if one_file:
        _logger.debug(f"one_file: {one_file}")
        project_path = cfg.SCRIPT_PATH / project_name
        project_downloader = FileDownloader(url=url, filepath=project_path)
    else:
        project_path = cfg.PROJECT_PATH / project_name
        project_downloader = ProjectDownloder(url=url, projectpath=project_path)

    if project_name in project_db:
        project_info: ProjectInfo = project_db[project_name]
        project_info.url = url
        project_info.one_file = one_file  # 需要检查是否相等，不想等要做清理，或者报错。
        project_info.project_path = str(project_path)
        project_info.upgrade_at = created_at
    else:
        project_info = ProjectInfo(
            name=project_name,
            one_file=one_file,
            url=url,
            project_path=str(project_path),
            created_at=created_at,
            upgrade_at=created_at,
        )

    if one_file:
        project_downloader.download()
    else:
        project_downloader.download()

    project_db[project_name] = project_info


def upgrade_project(project_name: str):
    project_info: ProjectInfo = project_db.get(project_name)
    if not project_info:
        raise errors.ProjectNotFoundError(project_name)

    pull_project(
        url=project_info.url,
        name=project_info.name,
        one_file=project_info.one_file,
    )


def remove_project(project_name: str):
    project_info: ProjectInfo = project_db.get(project_name)
    if not project_info:
        raise errors.ProjectNotFoundError(project_name)

    # TODO: 这里需要删除定时任务,或者对存在定时任务的工程报错。

    if project_info.one_file:
        base_path = cfg.SCRIPT_PATH
    else:
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

    task = UvTask(name=name, cmd=task_info.command, project_path=project_info.project_path)

    scheduler.add_job(func=task.run, trigger=task_info.cron, job_id=name)

    task_db[name] = task_info


def remove_task(task_name: str):
    if task_name not in task_db:
        raise errors.TaskNotFoundError(task_name)

    scheduler.remove_job(task_name)

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
    scheduler.run_job(task_name)

    return task_info


def sync_task():
    tasks = set(task_db.keys())
    jobs = set(job.id for job in scheduler.jobs)
    for task_name in tasks - jobs:
        del task_db[task_name]
    for job_name in jobs - tasks:
        scheduler.remove_job(job_name)
