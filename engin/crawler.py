import asyncio
from asyncio import Queue
from typing import List

from engin.downloader import Downloader, NetworkError, HTTPError, ContentError
from engin.spider import Spider, ScrapingError

WORKERS = 4


class Crawler:
    """Executes tasks received from spiders in asynchronous loop. Results are sent back to spiders for
    processing. Implements the sequence of tasks and spiders execution. Implements logic of handling errors
    raised by downloader and spiders.
    """

    def __init__(self, spiders: List[Spider], workers=WORKERS, on_complete=None, loop=None):
        self._workers = workers
        self._on_complete = on_complete

        self._spiders = Queue()
        self._loop = loop or asyncio.get_event_loop()

        self._init(spiders)

    def _init(self, spiders):
        for spider in spiders:
            self._spiders.put_nowait(spider)

    async def run(self):
        workers_tasks = [asyncio.Task(self._work(), loop=self._loop) for _ in range(self._workers)]

        await self._spiders.join()

        for t in workers_tasks:
            t.cancel()

    async def _work(self):
        while True:
            spider = await self._spiders.get()

            async with Downloader() as downloader:
                frontier = spider.get_frontier()
                for task in frontier:
                    try:
                        result = await downloader.request(**task.request_data)
                    except HTTPError as e:
                        await self._handle_http_error(frontier, task, e)
                        continue
                    except ContentError:
                        await self._handle_content_error(frontier, task)
                        continue
                    except NetworkError:
                        await self._handle_network_error(frontier, task)
                        continue

                    try:
                        await task.handler(result)
                    except ScrapingError:
                        await self._handle_scraping_error(frontier, task)
                        continue

            if self._on_complete is not None:
                self._on_complete(spider)

            self._spiders.task_done()

    async def _handle_http_error(self, frontier, task, error):
        pass

    async def _handle_network_error(self, frontier, task):
        pass

    async def _handle_content_error(self, frontier, task):
        pass

    async def _handle_scraping_error(self, frontier, task):
        pass
