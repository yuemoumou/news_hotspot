import feedparser
import requests


def crawl_rss(
    url,
    source_name
):

    # 用 requests 先获取内容（带超时），再交给 feedparser 解析
    try:
        resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        feed = feedparser.parse(resp.content)
    except Exception as e:
        print(f"RSS抓取失败 [{source_name}]: {e}")
        return []

    news = []

    for entry in feed.entries:

        title = getattr(
            entry,
            "title",
            ""
        )

        link = getattr(
            entry,
            "link",
            ""
        )

        if not title:
            continue

        if not link:
            continue

        news.append({

            "title": title,

            "url": link,

            "source": source_name

        })

    return news