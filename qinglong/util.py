import asyncio


def create_task(coro, name=None, tasks: set = set()):
    task = asyncio.create_task(coro, name=name)
    tasks.add(task)
    task.add_done_callback(tasks.remove)
    return task
