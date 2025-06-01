import asyncio
import logging
import time
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.util import undefined
from sqlalchemy import create_engine, event

from .config import settings as cfg

_logger = logging.getLogger(__name__)


class Scheduler:
    def __init__(self):
        cfg.DB_PATH.mkdir(parents=True, exist_ok=True)
        jobstores = {"default": SQLAlchemyJobStore(engine=self.create_sqlite_engine())}
        self.scheduler = BackgroundScheduler(jobstores=jobstores)
        self.scheduler.start()

    @property
    def jobs(self):
        return self.scheduler.get_jobs()

    def create_sqlite_engine(self):
        def enable_wal(dbapi_conn, connection_record):
            dbapi_conn.execute("PRAGMA journal_mode=WAL;")
            # 推荐同时设置以下优化参数
            dbapi_conn.execute("PRAGMA synchronous=NORMAL;")
            dbapi_conn.execute("PRAGMA busy_timeout=5000;")  # 设置5秒超时

        # 创建带 WAL 的 SQLite 引擎
        engine = create_engine(
            url=f"sqlite:///{str(cfg.DB_PATH)}/jobs.sqlite",
            connect_args={"check_same_thread": False},  # 多线程必需
            pool_size=10,  # 连接池大小
            max_overflow=5,  # 最大溢出连接数
        )

        # 注册事件监听器 - 每个新连接都启用 WAL
        event.listen(engine, "connect", enable_wal)
        return engine

    def add_job(self, job_id, func, trigger, max_instances=1, **kwargs):
        try:
            trigger = int(trigger)
        except ValueError:
            pass

        if isinstance(trigger, str):
            trigger = CronTrigger.from_crontab(trigger)
        elif isinstance(trigger, int):
            trigger = IntervalTrigger(seconds=trigger)

        if max_instances is None:
            max_instances = undefined
        _logger.info(f"add_job: {job_id}, {trigger}, {max_instances}, {kwargs}")

        job = self.scheduler.add_job(func, id=job_id, trigger=trigger, max_instances=max_instances, **kwargs)
        return job

    def remove_job(self, job_id):
        self.scheduler.remove_job(job_id)

    def pause_job(self, job_id):
        self.scheduler.pause_job(job_id)

    def resume_job(self, job_id):
        self.scheduler.resume_job(job_id)

    def run_job(self, job_id, paused=False):
        now_time = datetime.now() + timedelta(microseconds=100)
        self.scheduler.modify_job(job_id, next_run_time=now_time)
        if paused:
            time.sleep(0.1)
            self.pause_job(job_id)


scheduler = Scheduler()

if __name__ == "__main__":
    scheduler.start()

    def job_func():
        print("Job executed")

    scheduler.add_job("job1", job_func, trigger=1)
    print("Job added")

    asyncio.sleep(10)
    scheduler.remove_job("job1")
    print("Job removed")
