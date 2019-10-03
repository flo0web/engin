from collections import deque

from engin.task import Task


class Frontier:
    """Encapsulates a queue of tasks.

     Frontier class objects control the flow of tasks between Spiders and Crawler."""

    def __init__(self, attempts_limit: int = 3):
        self._attempts_limit = attempts_limit

        self._tasks_queue = deque()
        self._known_tasks = set()

    def __iter__(self):
        return self

    def __next__(self):
        try:
            task = self._tasks_queue.pop()
        except IndexError:
            raise StopIteration
        else:
            return task

    def _register(self, task):
        """Appends task to the queue.

        Updates the counter of attempts. Checks the number of attempts with the limit set for the frontier. If the
        limit is reached, the task will be ignored. If the limit is set to None, then the task can be
        repeated indefinitely."""

        task.register_attempt()
        if self._attempts_limit is not None or task.attempts <= self._attempts_limit:
            self._tasks_queue.appendleft(task)

    def schedule(self, task: Task):
        """Appends tasks unique for the frontier. This method should be used to register all new requests."""

        if task not in self._known_tasks:
            self._known_tasks.add(task)
            self._register(task)

    def repeat(self, task: Task):
        """Re-appends tasks. Causes an error if the task is not known in the frontier. The method should be used
        for append tasks caused errors."""

        self._register(task)

    def next(self):
        """Retrieves the task from the queue."""

        return self._tasks_queue.pop()
