import asyncio
import logging
from typing import AsyncGenerator

from engin.frontier import Frontier
from engin.worker import WorkerFactory, WorkerError

logger = logging.getLogger(__name__)


class CrawlingError(Exception):
    pass


class Crawler:
    num_threads = 20

    def __init__(self, worker_factory: WorkerFactory = None):
        if worker_factory is None:
            worker_factory = WorkerFactory()

        self._worker_factory = worker_factory

    @property
    def _threads_limit(self):
        if not hasattr(self.__class__, 'semaphore'):
            setattr(self.__class__, 'semaphore', asyncio.Semaphore(self.__class__.num_threads))

        return getattr(self.__class__, 'semaphore')

    async def _handle_thread(self, thread: AsyncGenerator, results: asyncio.queues):
        async with self._threads_limit:
            try:
                async for data in thread:
                    await results.put((0, data))
            except asyncio.CancelledError:
                pass
            except WorkerError as e:
                await results.put((1, e))

    async def _run_threads(self, spider, results):
        worker = self._worker_factory.get_worker(spider)

        threads = [asyncio.create_task(
            self._handle_thread(worker.thread, results)
        ) for _ in range(spider.num_threads)]

        try:
            await spider.frontier.join()
        finally:
            for thread in threads:
                thread.cancel()

        # сигнал для окончания итерации по результатам, что бы прервать асинхронный генератор run,
        # хотя получается, что TODO: генератор можно закрыть методом aclose()
        await results.put((1, StopAsyncIteration()))

    def _get_frontier(self):
        return Frontier(attempts=10)

    async def run(self, spider):
        spider.set_frontier(frontier=self._get_frontier())

        results = asyncio.Queue(maxsize=1)

        run_threads_task = asyncio.create_task(self._run_threads(spider, results))

        logger.info('Spider was started', extra={'url': spider.url})

        try:
            while True:
                err, data = await results.get()
                if err:
                    try:
                        raise data
                    except StopAsyncIteration:
                        # перехватывает сигнал, кототый поступает в
                        # очередь в конце метода _run_threads
                        break
                    except WorkerError:
                        raise CrawlingError()
                else:
                    yield data
        finally:
            run_threads_task.cancel()
