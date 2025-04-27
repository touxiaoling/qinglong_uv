import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
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
        self.scheduler = AsyncIOScheduler(jobstores=jobstores)

    @property
    def jobs(self):
        return self.scheduler.get_jobs()

    async def start(self):
        self.scheduler.start()

    async def add_job(self, job_id, func, trigger, max_instances=1, **kwargs):
        if isinstance(trigger, str):
            trigger = CronTrigger.from_crontab(trigger)
        elif isinstance(trigger, int):
            trigger = IntervalTrigger(seconds=trigger)

        if max_instances is None:
            max_instances = undefined

        job = self.scheduler.add_job(func, id=job_id, trigger=trigger, max_instances=max_instances, **kwargs)
        return job

    async def remove_job(self, job_id):
        self.scheduler.remove_job(job_id)

    async def pause_job(self, job_id):
        self.scheduler.pause_job(job_id)

    async def resume_job(self, job_id):
        self.scheduler.resume_job(job_id)


scheduler = Scheduler()

if __name__ == "__main__":

    async def main():
        await scheduler.start()

        async def job_func():
            print("Job executed")

        await scheduler.add_job("job1", job_func, trigger=1)
        print("Job added")

        await asyncio.sleep(10)
        await scheduler.remove_job("job1")
        print("Job removed")

    asyncio.run(main())
