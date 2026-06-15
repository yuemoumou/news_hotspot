from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

from crawler.crawler_manager import crawl_all
from services.news_service import save_news
from services.site_service import update_site_stats


def crawl_job():

    print(
        f"\n[{datetime.now()}] 开始抓取..."
    )

    try:

        news = crawl_all()

        print(
            f"获取新闻: {len(news)}"
        )

        save_news(news)

        update_site_stats()

        print(
            "抓取完成"
        )

    except Exception as e:

        print(
            "抓取失败:",
            e
        )


def start_scheduler():

    scheduler = BackgroundScheduler(
        timezone="Asia/Shanghai"
    )

    scheduler.add_job(
        crawl_job,
        trigger="interval",
        minutes=30,
        id="news_crawler",
        replace_existing=True
    )

    scheduler.start()

    print(
        "APScheduler 已启动"
    )

    return scheduler