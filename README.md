Asynchronous website crawling framework
=======================================

Engin is a set of tools for developing scrapers and running them in an asynchronous environment.

### Basic example
```
>>> from engin import Spider, crawl
>>> class MySpider(Spider):
...    async def handle(self, resp):
...        raw = await resp.raw
...        self._save(len(raw))
>>> spider = MySpider('https://httpbin.org/links/5/1')
>>> results = crawl([spider])
>>> for result in results:
...    print(result)
[169]
```