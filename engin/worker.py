import asyncio
import inspect
import logging

from engin.downloader import Downloader, HTTPError, NetworkError, ContentError
from engin.frontier import AttemptsExceeded
from engin.proxy import ProxyService
from engin.spider import ScrapingError

logger = logging.getLogger(__name__)


class WorkerError(Exception):
    """Воркер не смог выполнить задачу. При выполнении задачи возникла ошибка. Например, не хватило попыток,
    что бы скачать исходник. или какая-то ошибка при парсинге исходника.

    При возникновении этой ошибки, воркер прекращает свою работу. Эта ошибка будт перехвачена
    краулером, который остановит остальные воркеры"""
    pass


class Worker:
    def __init__(self, spider):
        self._spider = spider

    def _repeat_task(self, task):
        try:
            self._spider.frontier.repeat(task)
        except AttemptsExceeded:
            logger.warning('Download attempts exceeded: %s', task.request_data)
            raise WorkerError()

    @property
    async def thread(self):
        async with Downloader() as downloader:
            while True:
                task = await self._spider.frontier.get()

                try:
                    response = await downloader.request(**task.request_data)
                except HTTPError as e:
                    if int(e.status) == 404:
                        logger.warning('Page not found: %s', task.request_data)
                        raise WorkerError()
                    else:
                        self._repeat_task(task)
                    continue
                except (NetworkError, ContentError):
                    self._repeat_task(task)
                    continue

                try:
                    if inspect.isasyncgenfunction(task.handler):
                        async for result in task.handler(response, **task.handler_kwargs):
                            yield result
                    else:
                        await task.handler(response, **task.handler_kwargs)
                except ScrapingError:
                    logger.warning('Error while scraping data: %s', task.request_data)
                    raise WorkerError()

                self._spider.frontier.task_done()


class WorkerFactory:
    worker_class = Worker

    def get_worker(self, spider):
        return self.worker_class(spider)


class ProxyWorker(Worker):
    def __init__(self, proxy_service: ProxyService, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._proxy_service = proxy_service

    def _get_proxy(self):
        proxy = None
        if self._proxy_service is not None:
            proxy = self._proxy_service.get_proxy()

        return proxy

    @property
    async def thread(self):
        while True:
            task = await self._spider.frontier.get()
            async with Downloader() as downloader:
                try:
                    response = await downloader.request(proxy=self._get_proxy(), **task.request_data)
                except HTTPError as e:
                    if int(e.status) == 404:
                        logger.warning('Page not found: %s', task.request_data)
                        raise WorkerError()
                    else:
                        self._repeat_task(task)
                    continue
                except (NetworkError, ContentError):
                    self._repeat_task(task)
                    continue
                except asyncio.CancelledError:
                    continue

            try:
                if inspect.isasyncgenfunction(task.handler):
                    async for result in task.handler(response, **task.handler_kwargs):
                        yield result
                else:
                    await task.handler(response, **task.handler_kwargs)
            except ScrapingError:
                logger.warning('Error while scraping data: %s', task.request_data)
                raise WorkerError()

            self._spider.frontier.task_done()


class ProxyWorkerFactory(WorkerFactory):
    worker_class = ProxyWorker

    def __init__(self, proxy_service: ProxyService = None):
        self._proxy_service = proxy_service

    def get_worker(self, spider):
        return self.worker_class(spider=spider, proxy_service=self._proxy_service)
