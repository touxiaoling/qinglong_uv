import logging
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlencode

import httpx2

from . import runs
from .config import settings as cfg
from .models import RunStatus

logger = logging.getLogger(__name__)
_executor: ThreadPoolExecutor | None = None


def start():
    global _executor
    if cfg.NOTIFY_WEBHOOK_URL:
        _executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="notify")


def shutdown():
    global _executor
    if _executor is not None:
        _executor.shutdown(wait=True, cancel_futures=True)
        _executor = None


def enqueue(task_id: str, project: str, task: str, run_id: int, status: RunStatus):
    if _executor is not None and status in {"failed", "timed_out", "succeeded"}:
        _executor.submit(_notify, task_id, project, task, run_id, status)


def _notify(task_id: str, project: str, task: str, run_id: int, status: RunStatus):
    failures, delivered = runs.alert_state(task_id)
    event = None
    if status == "succeeded":
        if delivered:
            event = "recovered"
        failures = 0
    else:
        failures += 1
        if delivered == 0:
            event = "failed"
        elif delivered == 1 and failures >= 3:
            event = "still_failing"

    if event is not None:
        payload = {
            "event": event,
            "project": project,
            "task": task,
            "run_id": run_id,
            "status": status,
            "consecutive_failures": failures,
        }
        if cfg.PANEL_PUBLIC_URL:
            query = urlencode({"task": task, "run": run_id})
            payload["run_url"] = f"{cfg.PANEL_PUBLIC_URL.rstrip('/')}/?{query}"
        try:
            httpx2.post(cfg.NOTIFY_WEBHOOK_URL, json=payload, timeout=5).raise_for_status()
        except (httpx2.HTTPError, httpx2.InvalidURL) as exc:
            logger.warning("Could not deliver %s for task %s (%s)", event, task, type(exc).__name__)
        else:
            delivered = {"failed": 1, "still_failing": 2, "recovered": 0}[event]
    runs.save_alert_state(task_id, failures, delivered)
