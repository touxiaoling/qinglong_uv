import sqlite3
from collections import deque
from contextlib import closing
from datetime import datetime, timezone

from .config import settings as cfg
from .models import RunDetail, RunInfo, RunSource, RunStatus

_retained_runs = 100


def _connect():
    conn = sqlite3.connect(cfg.DB_PATH / "runs.sqlite")
    conn.row_factory = sqlite3.Row
    return closing(conn)


def _utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def create_tables():
    cfg.DB_PATH.mkdir(parents=True, exist_ok=True)
    with _connect() as conn, conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                source TEXT NOT NULL,
                status TEXT NOT NULL,
                scheduled_at TEXT NOT NULL,
                started_at TEXT,
                finished_at TEXT,
                exit_code INTEGER,
                reason TEXT,
                "commit" TEXT,
                output TEXT
            );
            CREATE INDEX IF NOT EXISTS runs_by_task ON runs (task_id, scheduled_at DESC, id DESC);
            CREATE TABLE IF NOT EXISTS alert_state (
                task_id TEXT PRIMARY KEY,
                failures INTEGER NOT NULL,
                delivered INTEGER NOT NULL
            );
        """)


def interrupt_running():
    with _connect() as conn, conn:
        conn.execute(
            "UPDATE runs SET status = 'interrupted', finished_at = ?, reason = ? WHERE status = 'running'",
            (_utc(datetime.now(timezone.utc)), "Service restarted before the run finished"),
        )


def _trim(conn, task_id: str):
    conn.execute(
        """DELETE FROM runs WHERE id IN (
            SELECT id FROM runs WHERE task_id = ? AND status != 'running'
            ORDER BY scheduled_at DESC, id DESC LIMIT -1 OFFSET ?
        )""",
        (task_id, _retained_runs),
    )


def start_run(task_id: str, source: RunSource, scheduled_at: datetime, commit: str | None) -> int:
    with _connect() as conn, conn:
        cursor = conn.execute(
            """INSERT INTO runs (task_id, source, status, scheduled_at, started_at, "commit")
            VALUES (?, ?, 'running', ?, ?, ?)""",
            (task_id, source, _utc(scheduled_at), _utc(datetime.now(timezone.utc)), commit),
        )
        assert cursor.lastrowid is not None
        return cursor.lastrowid


def finish_run(task_id: str, run_id: int, status: RunStatus, code: int | None, reason: str | None, output: str):
    with _connect() as conn, conn:
        conn.execute(
            "UPDATE runs SET status = ?, finished_at = ?, exit_code = ?, reason = ?, output = ? WHERE id = ?",
            (status, _utc(datetime.now(timezone.utc)), code, reason, output, run_id),
        )
        _trim(conn, task_id)


def skip_runs(task_id: str, source: RunSource, times: list[datetime], reason: str):
    ended = _utc(datetime.now(timezone.utc))
    with _connect() as conn, conn:
        conn.executemany(
            "INSERT INTO runs (task_id, source, status, scheduled_at, finished_at, reason) VALUES (?, ?, 'skipped', ?, ?, ?)",
            [(task_id, source, _utc(when), ended, reason) for when in times[-_retained_runs:]],
        )
        _trim(conn, task_id)


_summary_fields = 'id, source, status, scheduled_at, started_at, finished_at, exit_code, reason, "commit"'


def list_runs(task_id: str | None, limit: int = _retained_runs) -> list[RunInfo]:
    if task_id is None:
        return []
    with _connect() as conn:
        rows = conn.execute(
            f"SELECT {_summary_fields} FROM runs WHERE task_id = ? ORDER BY scheduled_at DESC, id DESC LIMIT ?",
            (task_id, limit),
        )
        return [RunInfo.model_validate(dict(row)) for row in rows]


def get_run(task_id: str, run_id: int) -> RunDetail | None:
    with _connect() as conn:
        row = conn.execute(
            f"SELECT {_summary_fields}, output FROM runs WHERE task_id = ? AND id = ?", (task_id, run_id)
        ).fetchone()
    return RunDetail.model_validate(dict(row)) if row else None


def alert_state(task_id: str) -> tuple[int, int]:
    with _connect() as conn:
        row = conn.execute("SELECT failures, delivered FROM alert_state WHERE task_id = ?", (task_id,)).fetchone()
    return (row["failures"], row["delivered"]) if row else (0, 0)


def save_alert_state(task_id: str, failures: int, delivered: int):
    with _connect() as conn, conn:
        conn.execute("REPLACE INTO alert_state (task_id, failures, delivered) VALUES (?, ?, ?)", (task_id, failures, delivered))


class RunOutput:
    """A bounded tail of this run's output, independent of the task log."""

    def __init__(self):
        self.lines: deque[str] = deque()
        self.size = 0

    def append(self, line: str):
        line = line[-63_999:]
        self.lines.append(line)
        self.size += len(line) + 1
        while self.size > 64_000 or len(self.lines) > 1000:
            self.size -= len(self.lines.popleft()) + 1

    def text(self) -> str:
        return "\n".join(self.lines)
