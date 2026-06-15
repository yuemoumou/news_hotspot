import requests
from bs4 import BeautifulSoup


def crawl_ithome():

    url = "https://www.ithome.com"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    news = []

    try:

        response = requests.get(
            url,
            headers=headers,
            timeout=10
        )

        response.encoding = "utf-8"

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        for a in soup.find_all("a"):

            title = a.get_text(
                strip=True
            )

            href = a.get("href")

            if not title:
                continue

            if len(title) < 10:
                continue

            if not href:
                continue

            if href.startswith("//"):
                href = "https:" + href

            news.append({

                "title": title,

                "url": href,

                "source": "IT之家"

            })

    except Exception as e:

        print(
            "IT之家抓取失败:",
            e
        )

    return news