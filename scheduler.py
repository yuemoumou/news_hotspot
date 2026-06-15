from services.scheduler_service import (
    start_scheduler,
    crawl_job
)

import time


if __name__ == "__main__":

    print(
        "新闻自动抓取服务启动..."
    )

    # 启动先抓一次

    crawl_job()

    # 启动定时器

    start_scheduler()

    while True:

        time.sleep(60)