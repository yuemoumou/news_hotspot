import requests
import xml.etree.ElementTree as ET


def crawl_36kr():

    rss_url = "https://36kr.com/feed"

    news = []

    try:

        response = requests.get(
            rss_url,
            timeout=10
        )

        root = ET.fromstring(
            response.content
        )

        for item in root.iter("item"):

            title = item.findtext(
                "title"
            )

            link = item.findtext(
                "link"
            )

            if title and link:

                news.append({

                    "title": title,

                    "url": link,

                    "source": "36氪"

                })

    except Exception as e:

        print(
            "36氪抓取失败:",
            e
        )

    return news