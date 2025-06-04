import pytest
from pathlib import Path
from datetime import datetime
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
    sync_project,
    init_task,
    sync_task,
)
from qinglong.models import ProjectInfo, TaskInfo, TaskStatus
from qinglong.database import project_db, task_db
from qinglong import errors

# 测试数据
TEST_PROJECT_URL = "https://github.com/test/repo.git"
TEST_PROJECT_NAME = "test-repo"
TEST_TASK_NAME = "test-task"
TEST_CRON = "*/5 * * * *"
TEST_CMD = "echo 'test'"


@pytest.fixture(autouse=True)
def setup_teardown():
    """每个测试前后的设置和清理"""
    # 清理数据库
    project_db.clear()
    task_db.clear()
    yield
    # 测试后清理
    project_db.clear()
    task_db.clear()


def test_list_projects():
    """测试列出项目列表"""
    # 添加测试项目
    project_info = ProjectInfo(
        name=TEST_PROJECT_NAME,
        url=TEST_PROJECT_URL,
        project_path="/test/path",
        created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        upgrade_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )
    project_db[TEST_PROJECT_NAME] = project_info

    # 测试列表功能
    projects = list_projects()
    assert len(projects) == 1
    assert projects[0]["name"] == TEST_PROJECT_NAME
    assert projects[0]["url"] == TEST_PROJECT_URL


def test_list_tasks():
    """测试列出任务列表"""
    # 添加测试任务
    task_info = TaskInfo(
        name=TEST_TASK_NAME,
        project_name=TEST_PROJECT_NAME,
        cron=TEST_CRON,
        command=TEST_CMD,
        created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        upgrade_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        status=TaskStatus.STARTED,
    )
    task_db[TEST_TASK_NAME] = task_info

    # 测试列表功能
    tasks = list_tasks()
    assert len(tasks) == 1
    assert tasks[0]["name"] == TEST_TASK_NAME
    assert tasks[0]["project_name"] == TEST_PROJECT_NAME


@pytest.mark.skip(reason="no test project")
def test_clone_project():
    """测试克隆项目"""
    # 测试克隆新项目
    clone_project(TEST_PROJECT_URL, TEST_PROJECT_NAME)
    assert TEST_PROJECT_NAME in project_db
    project_info = project_db[TEST_PROJECT_NAME]
    assert project_info.url == TEST_PROJECT_URL


@pytest.mark.skip(reason="no test project")
def test_remove_project():
    """测试删除项目"""
    # 先添加项目
    project_info = ProjectInfo(
        name=TEST_PROJECT_NAME,
        url=TEST_PROJECT_URL,
        project_path="/test/path",
        created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        upgrade_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )
    project_db[TEST_PROJECT_NAME] = project_info

    # 测试删除不存在的项目
    with pytest.raises(errors.ProjectNotFoundError):
        remove_project("non-existent-project")

    # 测试删除存在的项目
    remove_project(TEST_PROJECT_NAME)
    assert TEST_PROJECT_NAME not in project_db


def test_set_task():
    """测试设置任务"""
    # 先添加项目
    project_info = ProjectInfo(
        name=TEST_PROJECT_NAME,
        url=TEST_PROJECT_URL,
        project_path="/test/path",
        created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        upgrade_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )
    project_db[TEST_PROJECT_NAME] = project_info

    # 测试设置任务
    set_task(TEST_TASK_NAME, TEST_PROJECT_NAME, TEST_CRON, TEST_CMD)
    assert TEST_TASK_NAME in task_db
    task_info = task_db[TEST_TASK_NAME]
    assert task_info.project_name == TEST_PROJECT_NAME
    assert task_info.cron == TEST_CRON
    assert task_info.command == TEST_CMD


def test_remove_task():
    """测试删除任务"""
    # 先添加任务
    task_info = TaskInfo(
        name=TEST_TASK_NAME,
        project_name=TEST_PROJECT_NAME,
        cron=TEST_CRON,
        command=TEST_CMD,
        created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        upgrade_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        status=TaskStatus.STARTED,
    )
    task_db[TEST_TASK_NAME] = task_info

    # 测试删除不存在的任务
    with pytest.raises(errors.TaskNotFoundError):
        remove_task("non-existent-task")

    # 测试删除存在的任务
    remove_task(TEST_TASK_NAME)
    assert TEST_TASK_NAME not in task_db


@pytest.mark.skip(reason="no test project")
def test_task_status_operations():
    """测试任务状态相关操作"""
    # 先添加任务
    task_info = TaskInfo(
        name=TEST_TASK_NAME,
        project_name=TEST_PROJECT_NAME,
        cron=TEST_CRON,
        command=TEST_CMD,
        created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        upgrade_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        status=TaskStatus.STARTED,
    )
    task_db[TEST_TASK_NAME] = task_info

    # 测试暂停任务
    paused_task = pause_task(TEST_TASK_NAME)
    assert paused_task.status == TaskStatus.PAUSED

    # 测试启动任务
    started_task = start_task(TEST_TASK_NAME)
    assert started_task.status == TaskStatus.STARTED

    # 测试运行任务
    run_task(TEST_TASK_NAME)
    assert task_db[TEST_TASK_NAME].status == TaskStatus.STARTED


@pytest.mark.skip(reason="no test project")
def test_sync_operations():
    """测试同步操作"""
    # 添加测试数据
    project_info = ProjectInfo(
        name=TEST_PROJECT_NAME,
        url=TEST_PROJECT_URL,
        project_path="/test/path",
        created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        upgrade_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )
    project_db[TEST_PROJECT_NAME] = project_info

    task_info = TaskInfo(
        name=TEST_TASK_NAME,
        project_name=TEST_PROJECT_NAME,
        cron=TEST_CRON,
        command=TEST_CMD,
        created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        upgrade_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        status=TaskStatus.STARTED,
    )
    task_db[TEST_TASK_NAME] = task_info

    # 测试项目同步
    sync_project()
    assert TEST_TASK_NAME in task_db

    # 测试任务同步
    sync_task()
    assert TEST_TASK_NAME in task_db
