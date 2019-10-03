import logging

from engin.downloader import HTTPMethod
from engin.frontier import Frontier
from engin.task import Task

logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/68.0.3440.106 Safari/537.36'
}


class Storage:
    def __init__(self):
        self._data = []

    def add(self, data):
        self._data.append(data)

    @property
    def data(self):
        return self._data


class ScrapingError(Exception):
    pass


class Spider:
    """Spider generates jobs for crawler and processes results. The spider describes a separate process
    that you are going to perform using a crawler. For example, it describes which pages of the website need to
    be loaded and how to process it.
    """

    def __init__(self, entry_point, frontier: Frontier = None, storage: Storage = None):
        self._entry_point = entry_point

        self._frontier = frontier or Frontier()
        self._storage = storage or Storage()

        self._init_frontier()

    def get_frontier(self):
        return self._frontier

    def get_result(self):
        return self._storage.data

    async def handle(self, resp):
        """This method will process the result of the entry point."""

        raise NotImplemented()

    def _save(self, data):
        self._storage.add(data)

    def _catch_error(self, handler):
        async def wrapper(response):
            try:
                await handler(response)
            except Exception:
                logger.exception('Error when scraping %s' % self._entry_point)
                raise ScrapingError()

        return wrapper

    def _create_task(self, url: str, handler, method: HTTPMethod = HTTPMethod.GET, data: dict = None,
                     headers: dict = None):
        """Creates a task and registers it in the frontier."""

        assert self._frontier is not None

        request = Task(url, self._catch_error(handler), method, data, headers)

        self._frontier.schedule(request)

    def _init_frontier(self):
        """Creates a task with an entry point."""

        self._create_task(self._entry_point, handler=self.handle)

    def _get_headers(self):
        headers = dict(DEFAULT_HEADERS)
        return headers
