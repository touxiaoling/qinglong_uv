import asyncio
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.util import undefined

from .config import settings as cfg

_logger = logging.getLogger(__name__)


class Scheduler:
    def __init__(self):
        cfg.DB_PATH.mkdir(parents=True, exist_ok=True)
        jobstores = {"default": SQLAlchemyJobStore(url=f"sqlite:///{str(cfg.DB_PATH)}/jobs.sqlite")}
        self.scheduler = BackgroundScheduler(jobstores=jobstores)

    @property
    def jobs(self):
        return self.scheduler.get_jobs()

    def start(self):
        self.scheduler.start()

    def add_job(self, job_id, func, trigger, max_instances=1, **kwargs):
        if isinstance(trigger, str):
            trigger = CronTrigger.from_crontab(trigger)
        elif isinstance(trigger, int):
            trigger = IntervalTrigger(seconds=trigger)

        if max_instances is None:
            max_instances = undefined

        job = self.scheduler.add_job(func, id=job_id, trigger=trigger, max_instances=max_instances, **kwargs)
        return job

    def remove_job(self, job_id):
        self.scheduler.remove_job(job_id)

    def pause_job(self, job_id):
        self.scheduler.pause_job(job_id)

    def resume_job(self, job_id):
        self.scheduler.resume_job(job_id)

    def run_job(self, job_id):
        self.scheduler.modify_job(job_id, next_run_time=datetime.now())


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
