from datetime import datetime
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.job import Job
from apscheduler.jobstores.base import JobLookupError
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.triggers.base import BaseTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.util import undefined


class Scheduler:
    def __init__(self):
        jobstores = {"default": MemoryJobStore()}
        self.scheduler = BackgroundScheduler(jobstores=jobstores)
        self.executor = ThreadPoolExecutor()

    def start(self, paused=False):
        self.scheduler.add_executor(self.executor)
        self.scheduler.start(paused=paused)

    def shutdown(self, wait=False):
        self.scheduler.shutdown(wait=wait)
        self.scheduler.remove_executor("default", shutdown=False)
        self.executor = ThreadPoolExecutor()

    @property
    def jobs(self):
        return self.scheduler.get_jobs()

    def get_job(self, job_id):
        return self.scheduler.get_job(job_id)

    def parse_trigger(self, trigger: str | int):
        try:
            trigger = int(trigger)
        except ValueError:
            pass

        if isinstance(trigger, str):
            return CronTrigger.from_crontab(trigger, timezone=self.scheduler.timezone)
        if trigger <= 0:
            raise ValueError("The interval must be greater than zero.")
        try:
            return IntervalTrigger(seconds=trigger, timezone=self.scheduler.timezone)
        except OverflowError as exc:
            raise ValueError("The interval is too large.") from exc

    def add_job(self, job_id, func, trigger: str | int | BaseTrigger, paused=False, max_instances=1, **kwargs):
        if not isinstance(trigger, BaseTrigger):
            trigger = self.parse_trigger(trigger)
        if max_instances is None:
            max_instances = undefined
        if paused:
            kwargs["next_run_time"] = None
        return self.scheduler.add_job(func, id=job_id, trigger=trigger, max_instances=max_instances, **kwargs)

    def remove_job(self, job_id):
        self.scheduler.remove_job(job_id)

    def pause_job(self, job_id):
        self.scheduler.pause_job(job_id)

    def resume_job(self, job_id):
        self.scheduler.resume_job(job_id)

    def run_job(self, job_id):
        job = self.get_job(job_id)
        if job is None:
            raise JobLookupError(job_id)
        # Sharing the ID keeps the same instance limit. Manually queued runs
        # have no scheduled misfire window.
        manual_job = Job(
            self.scheduler,
            id=job.id,
            func=job.func,
            args=job.args,
            kwargs=job.kwargs,
            trigger=job.trigger,
            max_instances=job.max_instances,
            misfire_grace_time=None,
        )
        self.executor.submit_job(manual_job, [datetime.now(self.scheduler.timezone)])


scheduler = Scheduler()
