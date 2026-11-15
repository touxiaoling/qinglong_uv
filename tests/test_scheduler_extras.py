from threading import Event
from unittest.mock import patch

import pytest
from apscheduler.util import undefined

from qinglong.scheduler import Scheduler


@pytest.fixture
def scheduler():
    s = Scheduler()
    s.start()
    yield s
    s.shutdown()


def test_add_job_passes_undefined_when_max_instances_none(scheduler: Scheduler):
    with patch.object(scheduler.scheduler, "add_job") as add_job:
        scheduler.add_job("mx", lambda: None, trigger=1, max_instances=None)
    kwargs = add_job.call_args[1]
    assert kwargs.get("max_instances") is undefined


def test_run_job_while_paused_preserves_schedule(scheduler: Scheduler):
    executed = Event()
    job = scheduler.add_job("paused_run", executed.set, trigger=120, paused=True)

    scheduler.run_job(job.id)

    assert executed.wait(2)
    assert scheduler.get_job(job.id).next_run_time is None
