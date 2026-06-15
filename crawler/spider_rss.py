import feedparser


def crawl_rss(
    url,
    source_name
):

    feed = feedparser.parse(
        url
    )

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