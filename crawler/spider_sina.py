import requests
from bs4 import BeautifulSoup


def crawl_sina():

    url = "https://tech.sina.com.cn"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=10
    )

    response.encoding = response.apparent_encoding

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    news = []

    for a in soup.find_all("a"):

        title = a.get_text(strip=True)

        href = a.get("href")

        if not title:
            continue

        if not href:
            continue

        if len(title) < 10:
            continue

        news.append({
            "title": title,
            "url": href,
            "source": "新浪科技"
        })

    return news