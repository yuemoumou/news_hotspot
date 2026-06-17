from concurrent.futures import ThreadPoolExecutor, as_completed
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


def _crawl_one_site(site):
    """抓取单个站点（供线程池调用）"""
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

            return data

        spider_name = site["spider"]

        spider = SPIDERS.get(
            spider_name
        )

        if not spider:

            print(
                "未找到Spider:",
                spider_name
            )

            return []

        data = spider()

        print(
            site["name"],
            len(data)
        )

        return data

    except Exception as e:

        print(
            site["name"],
            e
        )

        return []


def crawl_all():
    """并行抓取所有启用的新闻源"""
    sites = get_sites()

    enabled_sites = [s for s in sites if s["enabled"]]

    if not enabled_sites:
        return []

    news = []

    # 使用线程池并行抓取（I/O 密集型，线程数可设大一些）
    max_workers = min(len(enabled_sites), 8)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_crawl_one_site, site): site
            for site in enabled_sites
        }
        for future in as_completed(futures):
            site = futures[future]
            try:
                data = future.result()
                news.extend(data)
            except Exception as e:
                print(f"{site['name']} 抓取异常: {e}")

    return news