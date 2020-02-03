from typing import Any

from multidict import MultiDict

from engin.downloader import HTTPMethod


def dict_to_tuple(target):
    if not target or target is None:
        return ()

    if isinstance(target, (dict, MultiDict)):
        return tuple((k, dict_to_tuple(v) if isinstance(v, (dict, MultiDict, list)) else v) for k, v in target.items())
    elif isinstance(target, list):
        return tuple((dict_to_tuple(v) if isinstance(v, (dict, MultiDict, list)) else v) for v in target)
    elif isinstance(target, (str, bytes)):
        return target


class Task:
    """Encapsulates the information for the request and the address for processing the result. Jobs are checked
    for uniqueness in the frontier, therefore they support the comparison interface."""

    def __init__(self, url: str, handler,
                 method: HTTPMethod = HTTPMethod.GET, data: Any = None, json=False, headers: dict = None, **kwargs):
        self._url = url
        self._method = method
        self._headers = headers

        self._data = data
        self._frozen_data = dict_to_tuple(data)

        self._json = json

        self._handler = handler
        self._handler_kwargs = kwargs

        self._attempts = 0

    def __hash__(self):
        return hash(tuple([self._url, self._method, self._frozen_data]))

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented()

        return self._url == other._url and self._method == other._method and self._frozen_data == other._frozen_data

    @property
    def attempts(self):
        return self._attempts

    def register_attempt(self):
        self._attempts += 1

    @property
    def request_data(self):
        return dict(
            url=self._url,
            method=self._method,
            data=self._data,
            headers=self._headers,
            json=self._json
        )

    async def handler(self, result):
        return await self._handler(result, **self._handler_kwargs)
