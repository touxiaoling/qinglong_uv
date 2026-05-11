import pytest
from pathlib import Path
from datetime import datetime
from unittest.mock import MagicMock, patch

from qinglong import api as api_module
from qinglong.api import (
    list_projects,
    list_tasks,
    clone_project,
    pull_project,
    remove_project,
    set_task,
    remove_task,
    start_task,
    pause_task,
    run_task,
    get_task_logs,
    get_project_config,
    kill_task,
    sync_project,
    init_task,
    sync_task,
)
from qinglong.models import ProjectInfo, TaskInfo, TaskStatus
from qinglong.database import project_db, task_db
from qinglong.scheduler import scheduler
from qinglong.uvtask import UvTask
from qinglong import errors

# 测试数据
TEST_PROJECT_URL = "https://github.com/test/repo.git"
TEST_PROJECT_NAME = "test-repo"
TEST_TASK_NAME = "test-task"
TEST_CRON = "*/5 * * * *"
TEST_CMD = "echo 'test'"


def _clear_scheduler_jobs():
    for job in list(scheduler.jobs):
        scheduler.remove_job(job.id)


@pytest.fixture(autouse=True)
def setup_teardown():
    """每个测试前后的设置和清理"""
    project_db.clear()
    task_db.clear()
    api_module.task_dict.clear()
    _clear_scheduler_jobs()
    yield
    project_db.clear()
    task_db.clear()
    api_module.task_dict.clear()
    _clear_scheduler_jobs()


def _sample_project_info(project_path: str) -> ProjectInfo:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return ProjectInfo(
        name=TEST_PROJECT_NAME,
        url=TEST_PROJECT_URL,
        project_path=project_path,
        created_at=now,
        upgrade_at=now,
    )


def _sample_task_info(**kwargs) -> TaskInfo:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    defaults = dict(
        name=TEST_TASK_NAME,
        project_name=TEST_PROJECT_NAME,
        cron=TEST_CRON,
        command=TEST_CMD,
        created_at=now,
        upgrade_at=now,
        status=TaskStatus.STARTED,
    )
    defaults.update(kwargs)
    return TaskInfo.model_validate(defaults)


def test_list_projects():
    """测试列出项目列表"""
    project_info = _sample_project_info("/test/path")
    project_db[TEST_PROJECT_NAME] = project_info

    projects = list_projects()
    assert len(projects) == 1
    assert projects[0]["name"] == TEST_PROJECT_NAME
    assert projects[0]["url"] == TEST_PROJECT_URL


def test_list_tasks():
    """测试列出任务列表"""
    task_info = _sample_task_info()
    task_db[TEST_TASK_NAME] = task_info

    tasks = list_tasks()
    assert len(tasks) == 1
    assert tasks[0]["name"] == TEST_TASK_NAME
    assert tasks[0]["project_name"] == TEST_PROJECT_NAME


@patch("qinglong.api.ProjectDownloder")
def test_clone_project_new(mock_downloader_cls, tmp_path, monkeypatch):
    monkeypatch.setattr(api_module.cfg, "PROJECT_PATH", tmp_path)
    mock_inst = MagicMock()
    mock_downloader_cls.return_value = mock_inst

    clone_project(TEST_PROJECT_URL, TEST_PROJECT_NAME)

    assert TEST_PROJECT_NAME in project_db
    assert project_db[TEST_PROJECT_NAME].url == TEST_PROJECT_URL
    mock_inst.download.assert_called_once()


@patch("qinglong.api.ProjectDownloder")
def test_clone_project_updates_existing(mock_downloader_cls, tmp_path, monkeypatch):
    monkeypatch.setattr(api_module.cfg, "PROJECT_PATH", tmp_path)
    project_db[TEST_PROJECT_NAME] = _sample_project_info(str(tmp_path / TEST_PROJECT_NAME))
    mock_inst = MagicMock()
    mock_downloader_cls.return_value = mock_inst

    new_url = "https://github.com/test/other.git"
    clone_project(new_url, TEST_PROJECT_NAME)

    assert project_db[TEST_PROJECT_NAME].url == new_url
    mock_inst.download.assert_called_once()


@patch("qinglong.api.ProjectDownloder")
def test_clone_project_default_name_from_url(mock_downloader_cls, tmp_path, monkeypatch):
    monkeypatch.setattr(api_module.cfg, "PROJECT_PATH", tmp_path)
    mock_inst = MagicMock()
    mock_downloader_cls.return_value = mock_inst

    clone_project("https://github.com/org/myrepo.git", name=None)

    assert "myrepo.git" in project_db
    mock_inst.download.assert_called_once()


@patch("qinglong.api.clone_project")
def test_pull_project(mock_clone):
    project_db[TEST_PROJECT_NAME] = _sample_project_info("/p")

    pull_project(TEST_PROJECT_NAME)

    mock_clone.assert_called_once_with(url=TEST_PROJECT_URL, name=TEST_PROJECT_NAME)


def test_pull_project_not_found():
    with pytest.raises(errors.ProjectNotFoundError):
        pull_project("missing")


def test_remove_project_not_in_db():
    with pytest.raises(errors.ProjectNotFoundError):
        remove_project("nope")


def test_remove_project_path_missing_raises(tmp_path, monkeypatch):
    monkeypatch.setattr(api_module.cfg, "PROJECT_PATH", tmp_path)
    project_db["ghost"] = _sample_project_info(str(tmp_path / "ghost"))

    with pytest.raises(errors.ProjectNotFoundError):
        remove_project("ghost")


def test_remove_project_removes_directory(tmp_path, monkeypatch):
    monkeypatch.setattr(api_module.cfg, "PROJECT_PATH", tmp_path)
    proj_dir = tmp_path / TEST_PROJECT_NAME
    proj_dir.mkdir(parents=True)
    project_db[TEST_PROJECT_NAME] = _sample_project_info(str(proj_dir))

    remove_project(TEST_PROJECT_NAME)

    assert TEST_PROJECT_NAME not in project_db
    assert not proj_dir.exists()


def test_remove_project_removes_file_path(tmp_path, monkeypatch):
    monkeypatch.setattr(api_module.cfg, "PROJECT_PATH", tmp_path)
    proj_file = tmp_path / "single-file-proj"
    proj_file.write_text("x")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    project_db["single-file-proj"] = ProjectInfo(
        name="single-file-proj",
        url=TEST_PROJECT_URL,
        project_path=str(proj_file),
        created_at=now,
        upgrade_at=now,
    )

    remove_project("single-file-proj")

    assert "single-file-proj" not in project_db
    assert not proj_file.exists()


def test_get_project_config_prefers_config_file(tmp_path):
    pdir = tmp_path / "proj"
    pdir.mkdir()
    (pdir / "config.json").write_text("{}")
    project_db["cfgproj"] = _sample_project_info(str(pdir))

    cfg_path = get_project_config("cfgproj")

    assert cfg_path == pdir / "config.json"


def test_get_project_config_fallback_yaml(tmp_path):
    pdir = tmp_path / "proj2"
    pdir.mkdir()
    project_db["cfgproj2"] = _sample_project_info(str(pdir))

    cfg_path = get_project_config("cfgproj2")

    assert cfg_path == pdir / "config.yaml"


def test_set_task_project_not_found():
    with pytest.raises(errors.ProjectNotFoundError):
        set_task(TEST_TASK_NAME, "missing-project", TEST_CRON, TEST_CMD)


def test_set_task_creates_job_and_updates_existing(tmp_path, monkeypatch):
    monkeypatch.setattr(api_module.cfg, "PROJECT_PATH", tmp_path)
    project_db[TEST_PROJECT_NAME] = _sample_project_info(str(tmp_path / TEST_PROJECT_NAME))

    set_task(TEST_TASK_NAME, TEST_PROJECT_NAME, TEST_CRON, TEST_CMD)
    assert TEST_TASK_NAME in task_db
    assert TEST_TASK_NAME in api_module.task_dict
    assert any(j.id == TEST_TASK_NAME for j in scheduler.jobs)

    set_task(TEST_TASK_NAME, TEST_PROJECT_NAME, "0 * * * *", "echo ok", timeout=30)
    assert task_db[TEST_TASK_NAME].cron == "0 * * * *"
    assert task_db[TEST_TASK_NAME].command == "echo ok"
    assert task_db[TEST_TASK_NAME].timeout == 30


def test_set_task_wrong_project_raises(tmp_path, monkeypatch):
    monkeypatch.setattr(api_module.cfg, "PROJECT_PATH", tmp_path)
    project_db[TEST_PROJECT_NAME] = _sample_project_info(str(tmp_path / TEST_PROJECT_NAME))
    project_db["other"] = _sample_project_info(str(tmp_path / "other"))
    project_db["other"].name = "other"

    set_task(TEST_TASK_NAME, TEST_PROJECT_NAME, TEST_CRON, TEST_CMD)

    with pytest.raises(errors.SetTaskError):
        set_task(TEST_TASK_NAME, "other", TEST_CRON, TEST_CMD)


def test_remove_task():
    """删除任务（需先通过 set_task 注册调度任务）"""
    project_db[TEST_PROJECT_NAME] = _sample_project_info("/test/path")
    set_task(TEST_TASK_NAME, TEST_PROJECT_NAME, TEST_CRON, TEST_CMD)

    with pytest.raises(errors.TaskNotFoundError):
        remove_task("non-existent-task")

    remove_task(TEST_TASK_NAME)
    assert TEST_TASK_NAME not in task_db
    assert TEST_TASK_NAME not in api_module.task_dict


def test_start_pause_run_task(tmp_path, monkeypatch):
    monkeypatch.setattr(api_module.cfg, "PROJECT_PATH", tmp_path)
    project_db[TEST_PROJECT_NAME] = _sample_project_info(str(tmp_path / TEST_PROJECT_NAME))
    set_task(TEST_TASK_NAME, TEST_PROJECT_NAME, TEST_CRON, TEST_CMD)

    paused = pause_task(TEST_TASK_NAME)
    assert paused.status == TaskStatus.PAUSED

    started = start_task(TEST_TASK_NAME)
    assert started.status == TaskStatus.STARTED

    run_task(TEST_TASK_NAME)
    assert task_db[TEST_TASK_NAME].status == TaskStatus.STARTED


def test_run_task_when_paused(tmp_path, monkeypatch):
    monkeypatch.setattr(api_module.cfg, "PROJECT_PATH", tmp_path)
    project_db[TEST_PROJECT_NAME] = _sample_project_info(str(tmp_path / TEST_PROJECT_NAME))
    set_task(TEST_TASK_NAME, TEST_PROJECT_NAME, TEST_CRON, TEST_CMD)
    pause_task(TEST_TASK_NAME)

    with patch.object(scheduler, "run_job") as mock_run:
        run_task(TEST_TASK_NAME)
        mock_run.assert_called_once_with(TEST_TASK_NAME, paused=True)


def test_start_task_not_found():
    with pytest.raises(errors.TaskNotFoundError):
        start_task("missing-task")


def test_pause_task_not_found():
    with pytest.raises(errors.TaskNotFoundError):
        pause_task("missing-task")


def test_run_task_not_found():
    with pytest.raises(errors.TaskNotFoundError):
        run_task("missing-task")


def test_kill_task_not_found():
    with pytest.raises(errors.TaskNotFoundError):
        kill_task("missing-task")


def test_get_task_logs_task_not_in_database():
    with pytest.raises(errors.TaskNotFoundError):
        get_task_logs("missing-task")


def test_kill_task_not_running():
    project_db[TEST_PROJECT_NAME] = _sample_project_info("/p")
    task_db[TEST_TASK_NAME] = _sample_task_info()
    api_module.task_dict[TEST_TASK_NAME] = UvTask(name=TEST_TASK_NAME, cmd=TEST_CMD, project_path="/tmp", timeout=0)

    with pytest.raises(errors.TaskNotRunningError):
        kill_task(TEST_TASK_NAME)


def test_kill_task_success():
    mock_task = MagicMock()
    mock_task.is_running = True
    project_db[TEST_PROJECT_NAME] = _sample_project_info("/p")
    task_db[TEST_TASK_NAME] = _sample_task_info()
    api_module.task_dict[TEST_TASK_NAME] = mock_task

    kill_task(TEST_TASK_NAME)

    mock_task.kill.assert_called_once()


def test_get_task_logs_requires_task_instance():
    project_db[TEST_PROJECT_NAME] = _sample_project_info("/p")
    task_db[TEST_TASK_NAME] = _sample_task_info()

    with pytest.raises(errors.TaskNotFoundError):
        get_task_logs(TEST_TASK_NAME)


def test_get_task_logs_delegates_to_uvtask(tmp_path, monkeypatch):
    monkeypatch.setattr(api_module.cfg, "PROJECT_PATH", tmp_path)
    project_db[TEST_PROJECT_NAME] = _sample_project_info(str(tmp_path / TEST_PROJECT_NAME))
    set_task(TEST_TASK_NAME, TEST_PROJECT_NAME, TEST_CRON, TEST_CMD)
    mock_task = MagicMock()
    mock_task.get_logs.return_value = ["a", "b"]
    api_module.task_dict[TEST_TASK_NAME] = mock_task

    lines = get_task_logs(TEST_TASK_NAME, limit=10)

    assert lines == ["a", "b"]
    mock_task.get_logs.assert_called_once_with(limit=10)


@patch.object(UvTask, "cache_prune")
@patch.object(UvTask, "python_upgrade")
def test_init_task_skips_when_project_missing(mock_upgrade, mock_prune, tmp_path, monkeypatch):
    monkeypatch.setattr(api_module.cfg, "PROJECT_PATH", tmp_path)
    task_db[TEST_TASK_NAME] = _sample_task_info(project_name="no-such-project")

    init_task()

    assert TEST_TASK_NAME not in api_module.task_dict


@patch.object(UvTask, "cache_prune")
@patch.object(UvTask, "python_upgrade")
def test_init_task_loads_jobs(mock_upgrade, mock_prune, tmp_path, monkeypatch):
    monkeypatch.setattr(api_module.cfg, "PROJECT_PATH", tmp_path)
    project_db[TEST_PROJECT_NAME] = _sample_project_info(str(tmp_path / TEST_PROJECT_NAME))
    task_db[TEST_TASK_NAME] = _sample_task_info(status=TaskStatus.PAUSED)

    init_task()

    mock_upgrade.assert_called_once()
    mock_prune.assert_called_once()
    assert TEST_TASK_NAME in api_module.task_dict
    job_ids = [j.id for j in scheduler.jobs]
    assert TEST_TASK_NAME in job_ids


@patch.object(UvTask, "cache_prune")
@patch.object(UvTask, "python_upgrade")
def test_init_task_skips_when_job_already_registered(mock_upgrade, mock_prune, tmp_path, monkeypatch):
    monkeypatch.setattr(api_module.cfg, "PROJECT_PATH", tmp_path)
    project_db[TEST_PROJECT_NAME] = _sample_project_info(str(tmp_path / TEST_PROJECT_NAME))
    set_task(TEST_TASK_NAME, TEST_PROJECT_NAME, TEST_CRON, TEST_CMD)

    init_task()

    # 调度器上同 id 任务已存在则 init 跳过重复添加
    assert TEST_TASK_NAME in api_module.task_dict


def test_sync_project_removes_tasks_for_missing_project():
    project_db[TEST_PROJECT_NAME] = _sample_project_info("/p")
    task_db[TEST_TASK_NAME] = _sample_task_info()
    del project_db[TEST_PROJECT_NAME]

    sync_project()

    assert TEST_TASK_NAME not in task_db


def test_sync_task_removes_task_without_scheduler_job():
    project_db[TEST_PROJECT_NAME] = _sample_project_info("/p")
    task_db[TEST_TASK_NAME] = _sample_task_info()

    sync_task()

    assert TEST_TASK_NAME not in task_db


def test_sync_task_removes_orphan_scheduler_job():
    scheduler.add_job("orphan-job", lambda: None, trigger=60)

    sync_task()

    assert "orphan-job" not in [j.id for j in scheduler.jobs]


def test_sync_task_keeps_registered_task():
    project_db[TEST_PROJECT_NAME] = _sample_project_info("/p")
    set_task(TEST_TASK_NAME, TEST_PROJECT_NAME, TEST_CRON, TEST_CMD)

    sync_task()

    assert TEST_TASK_NAME in task_db
    assert TEST_TASK_NAME in [j.id for j in scheduler.jobs]
