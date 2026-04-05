import asyncio

import pytest

from qinglong.util import async_run, create_task


def test_create_task_removes_finished_from_tracker():
    tasks: set[asyncio.Task] = set()

    async def work():
        return 42

    async def runner():
        t = create_task(work(), name="n", tasks=tasks)
        assert t in tasks
        await t
        await asyncio.sleep(0)
        assert len(tasks) == 0

    asyncio.run(runner())


def test_async_run_schedules_coroutine():
    seen: list[int] = []

    @async_run
    async def worker():
        seen.append(1)

    async def runner():
        worker()
        await asyncio.sleep(0.05)

    asyncio.run(runner())
    assert seen == [1]
