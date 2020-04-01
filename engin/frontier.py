import asyncio

from engin.task import Task

DEFAULT_ATTEMPTS = 3


class FrontierError(Exception):
    pass


class AttemptsExceeded(FrontierError):
    pass


class Frontier:
    def __init__(self, attempts: int = DEFAULT_ATTEMPTS):
        self._attempts = attempts

        self._tasks = asyncio.Queue()
        self._known_tasks = set()

    def _schedule(self, task: Task):
        current_attempt = task.new_attempt()
        if self._attempts is None or current_attempt <= self._attempts:
            self._tasks.put_nowait(task)
        else:
            raise AttemptsExceeded()

    def schedule(self, task: Task):
        if task not in self._known_tasks:
            self._known_tasks.add(task)
            self._schedule(task)

    def repeat(self, task: Task):
        self._schedule(task)
        self._tasks.task_done()

    def get(self):
        return self._tasks.get()

    async def join(self):
        await self._tasks.join()

    def task_done(self):
        self._tasks.task_done()
