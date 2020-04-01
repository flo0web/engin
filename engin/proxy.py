from collections import deque


class ProxyService:
    def __init__(self, proxy_list):
        self._proxy_list = deque(proxy_list)

    def get_proxy(self):
        proxy = self._proxy_list.pop()
        self._proxy_list.appendleft(proxy)
        return proxy
