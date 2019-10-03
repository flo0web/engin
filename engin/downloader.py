import asyncio
import json
import logging
from enum import Enum

import aiohttp
from lxml import html

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 10


class HTTPMethod(Enum):
    GET = 'GET'
    POST = 'POST'


class Result:
    def __init__(self, resp):
        self._resp = resp

        self._html = None
        self._json = None

    @property
    async def raw(self):
        return await self._resp.text()

    @property
    async def html(self):
        if self._html is None:
            self._html = html.document_fromstring(await self.raw)

        return self._html

    @property
    async def json(self):
        if self._json is None:
            self._json = json.loads(await self.raw)

        return self._json

    def get_status(self):
        return self._resp.status

    def get_history(self):
        return self._resp.history

    def get_cookies(self):
        return self._resp.cookies

    def get_url(self):
        return str(self._resp.url)

    def get_headers(self):
        return self._resp.headers


class DownloadError(Exception):
    pass


class NetworkError(DownloadError):
    pass


class HTTPError(DownloadError):
    pass


class Downloader:
    def __init__(self, timeout: int = DEFAULT_TIMEOUT, ssl: bool = True):
        self._session = aiohttp.ClientSession(
            raise_for_status=True,
            timeout=aiohttp.ClientTimeout(total=timeout)
        )

        self._ssl = ssl

    async def request(self, url: str, method: HTTPMethod, data: dict = None, headers: dict = None):
        logger.info('Request starts: %s' % url)
        try:
            resp = await self._session.request(
                method=method.value,
                url=url,
                data=data,
                headers=headers,

                ssl=self._ssl
            )
        except aiohttp.ClientResponseError:
            logger.exception('Error when downloading url %s' % url)
            raise HTTPError()
        except (aiohttp.ClientError, asyncio.TimeoutError):
            logger.exception('Error when downloading url %s' % url)
            raise NetworkError()

        await resp.text()
        resp.release()

        return Result(resp)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args, **kwargs):
        await self._session.close()


