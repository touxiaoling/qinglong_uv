from asyncio import gather
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from threading import Lock
import logging
import tomllib
from typing import Annotated

import yaml
from apscheduler.executors.base import MaxInstancesReachedError
from apscheduler.jobstores.base import JobLookupError
from fastapi import APIRouter, FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from git import GitCommandError
from pydantic import BaseModel, Field, StringConstraints
from starlette.concurrency import run_in_threadpool

from . import api, errors
from .database import task_db
from .models import ProjectInfo, TaskInfo
from .scheduler import scheduler

logger = logging.getLogger(__name__)
web_dist = Path(__file__).with_name("web_dist")
router = APIRouter(prefix="/api")
project_changes = Lock()
task_changes = Lock()
NonEmpty = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class ProjectInput(BaseModel):
    url: NonEmpty
    name: NonEmpty | None = None


class ProjectConfig(BaseModel):
    filename: str
    content: str


class ConfigInput(BaseModel):
    content: str


class TaskSettings(BaseModel):
    cron: NonEmpty
    command: NonEmpty
    timeout: int = Field(default=0, ge=0)


class TaskInput(TaskSettings):
    name: NonEmpty
    project_name: NonEmpty


class TaskView(TaskInfo):
    is_running: bool
    next_run_at: datetime | None
    registered: bool


def task_view(task: TaskInfo) -> TaskView:
    job = scheduler.get_job(task.name)
    runner = api.task_dict.get(task.name)
    return TaskView(
        **task.model_dump(),
        is_running=runner is not None and runner.is_running,
        next_run_at=job.next_run_time if job else None,
        registered=job is not None,
    )


@router.get("/projects")
def projects() -> list[ProjectInfo]:
    with task_changes:
        return [ProjectInfo.model_validate(project) for project in api.list_projects()]


@router.post("/projects", status_code=204)
def clone_project(data: ProjectInput) -> None:
    with project_changes:
        api.clone_project(data.url, data.name)


@router.post("/projects/{name}/pull", status_code=204)
def pull_project(name: str) -> None:
    with project_changes:
        api.pull_project(name)


@router.delete("/projects/{name}", status_code=204)
def remove_project(name: str) -> None:
    with project_changes, task_changes:
        api.remove_project(name)


@router.get("/projects/{name}/config")
def read_config(name: str) -> ProjectConfig:
    with project_changes:
        path = api.get_project_config(name)
        return ProjectConfig(filename=path.name, content=path.read_text(encoding="utf-8") if path.exists() else "")


@router.put("/projects/{name}/config", status_code=204)
def save_config(name: str, data: ConfigInput) -> None:
    with project_changes:
        path = api.get_project_config(name)
        if path.suffix.lower() == ".toml":
            tomllib.loads(data.content)
        else:
            yaml.safe_load(data.content)
        path.write_text(data.content, encoding="utf-8")


@router.get("/tasks")
def tasks() -> list[TaskView]:
    with task_changes:
        return [task_view(task) for task in task_db.values()]


@router.post("/tasks", status_code=201)
def create_task(data: TaskInput) -> TaskView:
    with task_changes:
        if data.name in task_db:
            raise HTTPException(409, "A task with that name already exists.")
        return task_view(api.set_task(data.name, data.project_name, data.cron, data.command, data.timeout))


@router.put("/tasks/{name}")
def update_task(name: str, data: TaskSettings) -> TaskView:
    with task_changes:
        task = task_db.get(name)
        if task is None:
            raise errors.TaskNotFoundError(name)
        return task_view(api.set_task(name, task.project_name, data.cron, data.command, data.timeout))


@router.post("/sync", status_code=204)
def sync_tasks() -> None:
    with task_changes:
        api.sync_task()


@router.delete("/tasks/{name}", status_code=204)
def remove_task(name: str) -> None:
    with task_changes:
        api.remove_task(name)


@router.post("/tasks/{name}/resume")
def resume_task(name: str) -> TaskView:
    with task_changes:
        return task_view(api.start_task(name))


@router.post("/tasks/{name}/pause")
def pause_task(name: str) -> TaskView:
    with task_changes:
        return task_view(api.pause_task(name))


@router.post("/tasks/{name}/run", status_code=202)
def run_task(name: str) -> TaskView:
    with task_changes:
        return task_view(api.run_task(name))


@router.post("/tasks/{name}/kill", status_code=204)
def kill_task(name: str) -> None:
    with task_changes:
        api.kill_task(name)


@router.get("/tasks/{name}/logs")
def task_logs(name: str, response: Response, limit: Annotated[int, Query(ge=1, le=1000)] = 1000) -> list[str]:
    response.headers["Cache-Control"] = "no-store"
    with task_changes:
        return list(reversed(list(api.get_task_logs(name, limit))))


@asynccontextmanager
async def lifespan(_: FastAPI):
    scheduler.start(paused=True)
    try:
        await run_in_threadpool(api.init_task)
        scheduler.scheduler.resume()
        yield
    finally:
        scheduler.scheduler.pause()
        try:
            await gather(*(run_in_threadpool(runner.disable, stop_running=True) for runner in api.task_dict.values()))
        finally:
            await run_in_threadpool(scheduler.shutdown, wait=True)
            api.task_dict.clear()


app = FastAPI(title="Qinglong UV", lifespan=lifespan, docs_url="/api/docs", openapi_url="/api/openapi.json", redoc_url=None)
app.include_router(router)


@app.exception_handler(errors.ProjectNotFoundError)
@app.exception_handler(errors.TaskNotFoundError)
@app.exception_handler(JobLookupError)
async def not_found(_: Request, exc: Exception):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(errors.TaskNotRunningError)
@app.exception_handler(errors.TaskRunningError)
@app.exception_handler(errors.ProjectConflictError)
@app.exception_handler(errors.SetTaskError)
@app.exception_handler(MaxInstancesReachedError)
async def task_conflict(_: Request, exc: Exception):
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(ValueError)
@app.exception_handler(yaml.YAMLError)
async def invalid_value(_: Request, exc: Exception):
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.exception_handler(GitCommandError)
async def git_error(_: Request, exc: GitCommandError):
    logger.warning("Git operation failed with exit status %s", exc.status)
    return JSONResponse(status_code=502, content={"detail": "Git operation failed. Check the repository URL and access."})


@app.get("/", include_in_schema=False)
def index():
    path = web_dist / "index.html"
    if not path.is_file():
        raise HTTPException(503, "Build the frontend with npm --prefix frontend run build.")
    return FileResponse(path, headers={"Cache-Control": "no-cache"})


if (web_dist / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=web_dist / "assets"), name="assets")
