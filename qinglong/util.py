import asyncio
import functools


def create_task(coro, name=None, tasks: set = set()):
    task = asyncio.create_task(coro, name=name)
    tasks.add(task)
    task.add_done_callback(tasks.remove)
    return task


def async_run(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        create_task(func(*args, **kwargs))

    return wrapper
