from engin.downloader import HTTPMethod


class Task:
    """Encapsulates the information for the request and the address for processing the result. Jobs are checked
    for uniqueness in the frontier, therefore they support the comparison interface."""

    def __init__(self, url: str, handler, method: HTTPMethod = HTTPMethod.GET,
                 data: dict = None, headers: dict = None):
        self._url = url
        self._method = method
        self._headers = headers

        self._data = tuple((k, v) for k, v in data.items()) if data is not None else ()

        self._handler = handler

        self._attempts = 0

    def __hash__(self):
        return hash(tuple([self._url, self._method]) + self._data)

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented()

        return self._url == other._url and self._method == other._method and self._data == other._data

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
            headers=self._headers
        )

    @property
    def handler(self):
        return self._handler
