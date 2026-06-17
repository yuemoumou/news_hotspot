from datetime import datetime
import json

from database.db import get_conn


def save_news(news_list):

    conn = get_conn()

    insert_count = 0
    skip_count = 0

    for item in news_list:

        try:

            # ------------------
            # URL去重
            # ------------------

            exists = conn.execute(
                """
                SELECT 1
                FROM news
                WHERE url=?
                LIMIT 1
                """,
                (
                    item["url"],
                )
            ).fetchone()

            if exists:

                skip_count += 1

                continue

            crawl_time = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            title = item["title"]

            # ------------------
            # DeepSeek分析
            # ------------------

            ai_summary = ""
            category = ""
            keywords = ""
            sentiment_label = ""

            ai_summary = None
            category = None
            keywords = None
            sentiment_label = None

            # ------------------
            # 保存新闻
            # ------------------

            cursor = conn.execute(
            """
            INSERT INTO news(

            title,
            summary,
            url,
            source,
            publish_time,
            crawl_time,

            ai_summary,
            category,
            keywords,
            sentiment_label

            )

            VALUES(
            ?,?,?,?,?,?,?,?,?,?
            )
            """,
            (
                item["title"],
                item.get("summary",""),
                item["url"],
                item.get("source",""),
                item.get("publish_time"),
                crawl_time,

                ai_summary,
                category,
                keywords,
                sentiment_label
            )
            )

            news_id = cursor.lastrowid

            # ------------------
            # FTS同步（显式指定 rowid = news.id，保证搜索时行号一致）
            # ------------------

            try:

                conn.execute(
                    """
                    INSERT INTO news_fts(
                        rowid,
                        title,
                        source,
                        url
                    )
                    VALUES(
                        ?,?,?,?
                    )
                    """,
                    (
                        news_id,
                        item["title"],
                        item.get(
                            "source",
                            ""
                        ),
                        item["url"]
                    )
                )

            except Exception:

                pass

            insert_count += 1

        except Exception as e:

            print(
                "保存失败:",
                e
            )

    conn.commit()

    conn.close()

    print(
        f"新增:{insert_count} 跳过:{skip_count}"
    )