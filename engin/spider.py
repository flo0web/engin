import inspect
from typing import Any

from engin.downloader import HTTPMethod
from engin.frontier import Frontier
from engin.task import Task

DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/68.0.3440.106 Safari/537.36'
}


class ScrapingError(Exception):
    pass


class Spider:
    """Spider generates jobs for crawler and processes results. The spider describes a separate process
    that you are going to perform using a crawler. For example, it describes which pages of the website need to
    be loaded and how to process it.
    """

    name = None

    def __init__(self, entry_point):
        self._entry_point = entry_point

        self._frontier = None

    @property
    def frontier(self):
        return self._frontier

    @frontier.setter
    def frontier(self, frontier):
        self._frontier = frontier
        self._init_frontier()

    @property
    def url(self):
        return self._entry_point

    # deprecated
    def set_frontier(self, frontier: Frontier):
        self._frontier = frontier
        self._init_frontier()

    async def handle(self, resp):
        """This method will process the result of the entry point."""

        raise NotImplemented()

    def _catch_error(self, handler):
        async def wrapper(response, **kwargs):
            try:
                await handler(response, **kwargs)
            except Exception:
                raise ScrapingError()

        return wrapper

    def _catch_error_async_gen(self, handler):
        async def wrapper(response, **kwargs):
            try:
                async for data in handler(response, **kwargs):
                    yield data
            except Exception:
                raise ScrapingError()

        return wrapper

    def _create_task(self, url: str, handler, method: HTTPMethod = HTTPMethod.GET, data: Any = None, json=False,
                     headers: dict = None, encoding=None, **kwargs):
        """Creates a task and registers it in the frontier."""

        assert self._frontier is not None

        if headers is None:
            headers = self._headers

        wrapped_handler = self._catch_error_async_gen(handler) if inspect.isasyncgenfunction(
            handler
        ) else self._catch_error(handler)

        request = Task(url, wrapped_handler, method, data, json, headers, encoding, **kwargs)

        self._frontier.schedule(request)

    def _init_frontier(self):
        """Creates a task with an entry point."""

        self._create_task(self._entry_point, handler=self.handle)

    @property
    def _headers(self):
        return dict(DEFAULT_HEADERS)

    @classmethod
    def suitable_for(cls, url):
        return cls.name is not None and cls.name in url

    @classmethod
    def configure(cls, pattern, crawler, num_threads=1):
        cls._pattern = pattern
        cls.name = pattern

        cls._crawler = crawler
        cls._num_threads = num_threads

    def run(self):
        return self._crawler.run(self)
