import sys
from unittest.mock import MagicMock, patch

import pytest
from apscheduler.util import undefined

from qinglong.scheduler import Scheduler


@pytest.fixture
def scheduler():
    s = Scheduler()
    yield s
    for job in list(s.jobs):
        s.remove_job(job.id)


def test_create_sqlite_engine_registers_wal_listener(scheduler: Scheduler):
    mock_engine = MagicMock()
    mock_sa = MagicMock()
    mock_sa.create_engine.return_value = mock_engine
    mock_sa.event.listen = MagicMock()

    with patch.dict(sys.modules, {"sqlalchemy": mock_sa}):
        eng = scheduler.create_sqlite_engine()

    assert eng is mock_engine
    mock_sa.create_engine.assert_called_once()
    mock_sa.event.listen.assert_called_once()


def test_add_job_passes_undefined_when_max_instances_none(scheduler: Scheduler):
    with patch.object(scheduler.scheduler, "add_job") as add_job:
        scheduler.add_job("mx", lambda: None, trigger=1, max_instances=None)
    kwargs = add_job.call_args[1]
    assert kwargs.get("max_instances") is undefined


def test_run_job_when_paused_pauses_after_modify(scheduler: Scheduler):
    with patch("qinglong.scheduler.time.sleep"):
        scheduler.add_job("paused_run", lambda: None, trigger=120)
        scheduler.run_job("paused_run", paused=True)
