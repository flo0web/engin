import asyncio
from typing import List

from engin import Crawler, Spider


def crawl(spiders: List[Spider]):
    crawler = Crawler(spiders)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(crawler.run())

    loop.stop()
    loop.run_forever()

    loop.close()

    return [spider.get_result() for spider in spiders]
