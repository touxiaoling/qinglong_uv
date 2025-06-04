import pytest
import time
from datetime import datetime, timedelta
from qinglong.scheduler import Scheduler


@pytest.fixture
def scheduler():
    scheduler = Scheduler()
    yield scheduler
    # 清理所有任务
    for job in scheduler.jobs:
        scheduler.remove_job(job.id)


def test_add_job(scheduler: Scheduler):
    """测试添加任务"""

    def test_func():
        pass

    job = scheduler.add_job("test_job", test_func, trigger=1)
    assert job.id == "test_job"
    assert len(scheduler.jobs) == 1


def test_remove_job(scheduler: Scheduler):
    """测试删除任务"""

    def test_func():
        pass

    scheduler.add_job("test_job", test_func, trigger=1)
    assert len(scheduler.jobs) == 1

    scheduler.remove_job("test_job")
    assert len(scheduler.jobs) == 0


def test_pause_resume_job(scheduler: Scheduler):
    """测试暂停和恢复任务"""
    execution_count = 0

    def test_func():
        nonlocal execution_count
        execution_count += 1

    scheduler.add_job("test_job", test_func, trigger=1)
    time.sleep(1.1)  # 等待第一次执行
    assert execution_count == 1

    scheduler.pause_job("test_job")
    time.sleep(1.1)  # 等待一段时间
    assert execution_count == 1  # 暂停后不应该执行

    scheduler.resume_job("test_job")
    time.sleep(1.1)  # 等待恢复后执行
    assert execution_count == 2


def test_run_job(scheduler: Scheduler):
    """测试立即运行任务"""
    execution_count = 0

    def test_func():
        nonlocal execution_count
        execution_count += 1

    scheduler.add_job("test_job", test_func, trigger=10)  # 设置较长的间隔
    scheduler.run_job("test_job")  # 立即运行
    time.sleep(0.2)  # 等待执行
    assert execution_count == 1


def test_cron_trigger(scheduler: Scheduler):
    """测试 cron 触发器"""

    def test_func():
        pass

    job = scheduler.add_job("cron_job", test_func, trigger="* * * * *")
    assert job.trigger.fields[0].expressions[0].first == 0
    assert job.trigger.fields[0].expressions[0].last == 59


def test_max_instances(scheduler: Scheduler):
    """测试最大实例数限制"""
    execution_count = 0

    def test_func():
        nonlocal execution_count
        time.sleep(0.5)  # 模拟长时间运行的任务
        execution_count += 1

    scheduler.add_job("test_job", test_func, trigger=1, max_instances=1)
    time.sleep(1.1)  # 等待第一次执行
    assert execution_count == 1  # 由于 max_instances=1，应该只有一次执行
