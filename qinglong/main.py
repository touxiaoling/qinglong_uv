import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Body
from fastapi.responses import JSONResponse

from .config import settings as cfg
from .scheduler import scheduler
from . import api
from . import errors

_logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    cfg.TASK_LOG_PATH.mkdir(parents=True, exist_ok=True)
    cfg.SCRIPT_PATH.mkdir(parents=True, exist_ok=True)
    cfg.PROJECT_PATH.mkdir(parents=True, exist_ok=True)

    await scheduler.start()
    await api.sync_task()
    yield
    print("All tasks completed.")


app = FastAPI(title="Qinglong-uv", version="0.0.2", debug=cfg.DEBUG, lifespan=lifespan)


@app.get("/api/project_list")
async def get_project_list():
    projects = await api.get_project_list()
    projects = {k: v.model_dump() for k, v in projects.items()}
    return JSONResponse(content=projects)


@app.get("/api/task_list")
async def get_task_list():
    tasks = await api.get_task_list()
    tasks = {k: v.model_dump() for k, v in tasks.items()}
    return JSONResponse(content=tasks)


@app.post("/api/upload_script")
async def upload_script(name: str = Body(...), file: bytes = Body(...)):
    api.upload_script(name=name, contents=file)
    return JSONResponse({"res": "ok"})


@app.post("/api/pull_project")
async def pull_project(url: str = Body(...), name: str = Body(None), one_file: bool = Body(False)):
    await api.pull_project(url=url, name=name, one_file=one_file)
    return JSONResponse({"res": "ok"})


@app.post("/api/upgrade_project")
async def upgrade_project(project_name: str = Body(..., embed=True)):
    try:
        await api.upgrade_project(project_name=project_name)
    except errors.ProjectNotFoundError:
        return JSONResponse(status_code=404, content={"message": "Project not found"})

    return JSONResponse(status_code=200, content={"message": "Project upgraded successfully"})


@app.post("/api/remove_project")
async def remove_project(project_name: str = Body(..., embed=True)):
    try:
        await api.remove_project(project_name=project_name)

    except errors.ProjectNotFoundError:
        return JSONResponse(status_code=404, content={"message": "Project not found"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": f"Error removing project: {str(e)}"})

    return JSONResponse(status_code=200, content={"message": "Project removed successfully"})


@app.post("/api/set_task")
async def set_task(name: str = Body(...), project_name: str = Body(...), cron: str = Body(...), command: str = Body(...)):
    await api.set_task(name=name, project_name=project_name, cron=cron, cmd=command)

    return JSONResponse(status_code=200, content={"message": "Task added successfully"})


@app.post("/api/remove_task")
async def remove_task(task_name: str = Body(..., embed=True)):
    try:
        await api.remove_task(task_name=task_name)
    except errors.TaskNotFoundError:
        return JSONResponse(status_code=404, content={"message": "Task not found"})

    return JSONResponse(status_code=200, content={"message": "Task removed successfully"})


@app.post("/api/start_task")
async def start_task(task_name: str = Body(..., embed=True)):
    try:
        await api.start_task(task_name=task_name)
    except errors.TaskNotFoundError:
        return JSONResponse(status_code=404, content={"message": "Task not found"})

    return JSONResponse(status_code=200, content={"message": "Task started successfully"})


@app.post("/api/pause_task")
async def pause_task(task_name: str = Body(..., embed=True)):
    try:
        await api.pause_task(task_name=task_name)
    except errors.TaskNotFoundError:
        return JSONResponse(status_code=404, content={"message": "Task not found"})

    return JSONResponse(status_code=200, content={"message": "Task paused successfully"})


@app.post("/api/run_task")
async def run_task(task_name: str = Body(..., embed=True)):
    pass


@app.post("/api/stop_task")
async def stop_task(task_name: str = Body(..., embed=True)):
    pass
