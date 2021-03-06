import asyncio
import json
import logging
from enum import Enum
from typing import Any

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
    def __init__(self, error: aiohttp.ClientResponseError):
        self._error = error

    @property
    def status(self):
        return self._error.status


class ContentError(DownloadError):
    pass


class Downloader:
    def __init__(self, timeout: int = DEFAULT_TIMEOUT, ssl: bool = True):
        self._session = aiohttp.ClientSession(
            raise_for_status=True,
            timeout=aiohttp.ClientTimeout(total=timeout)
        )

        self._ssl = ssl

    async def request(self, url: str, method: HTTPMethod, data: Any = None, json=False,
                      headers: dict = None, proxy=None):
        logger.info('Request starts: %s' % {
            'url': url, 'method': method.value, 'data': data, 'json': json, 'headers': headers
        })

        request_kwargs = dict(
            url=url,
            method=method.value,
            headers=headers,
            proxy=proxy,

            ssl=self._ssl,
        )

        if json:
            request_kwargs['json'] = data
        else:
            request_kwargs['data'] = data

        try:
            resp = await self._session.request(**request_kwargs)
        except aiohttp.ClientResponseError as e:
            logger.debug('Error when downloading url %s' % {
                'url': url, 'method': method.value, 'data': data, 'headers': headers
            }, exc_info=True)
            raise HTTPError(e)
        except (aiohttp.ClientError, asyncio.TimeoutError):
            logger.debug('Error when downloading url %s' % {
                'url': url, 'method': method.value, 'data': data, 'headers': headers
            }, exc_info=True)
            raise NetworkError()
        except Exception:
            logger.exception('Error when downloading url %s' % {
                'url': url, 'method': method.value, 'data': data, 'headers': headers
            })
            raise NetworkError()

        try:
            await resp.text()
        except Exception:
            logger.exception('Error when downloading url %s' % {
                'url': url, 'method': method.value, 'data': data, 'headers': headers
            })
            raise ContentError()

        resp.release()

        return Result(resp)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args, **kwargs):
        await self._session.close()
