from services.site_service import get_sites

from crawler.spider_sina import crawl_sina
from crawler.spider_36kr import crawl_36kr
from crawler.spider_ithome import crawl_ithome
from crawler.spider_rss import crawl_rss


SPIDERS = {

    "crawl_sina":
        crawl_sina,

    "crawl_36kr":
        crawl_36kr,

    "crawl_ithome":
        crawl_ithome

}


def crawl_all():

    news = []

    sites = get_sites()

    for site in sites:

        if not site["enabled"]:
            continue

        try:

            if site["site_type"] == "rss":

                data = crawl_rss(

                    site["url"],

                    site["name"]

                )

                print(
                    site["name"],
                    len(data)
                )

                news.extend(
                    data
                )

                continue

            spider_name = site["spider"]

            spider = SPIDERS.get(
                spider_name
            )

            if not spider:

                print(
                    "未找到Spider:",
                    spider_name
                )

                continue

            data = spider()

            print(
                site["name"],
                len(data)
            )

            news.extend(
                data
            )

        except Exception as e:

            print(
                site["name"],
                e
            )

    return news