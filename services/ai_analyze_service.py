import json
import time

from database.db import get_conn
from services.deepseek_service import analyze_news


def _parse_ai_result(result):

    result = result.replace(
        "```json",
        ""
    )

    result = result.replace(
        "```",
        ""
    )

    result = result.strip()

    return json.loads(result)


def _save_ai_result(
    conn,
    news_id,
    data
):

    conn.execute(
        """
        UPDATE news
        SET

            ai_summary=?,

            category=?,

            keywords=?,

            sentiment_label=?

        WHERE id=?
        """,
        (
            data.get(
                "summary",
                ""
            ),
            data.get(
                "category",
                ""
            ),
            data.get(
                "keywords",
                ""
            ),
            data.get(
                "sentiment",
                ""
            ),
            news_id
        )
    )


def analyze_one_news(news_id):

    conn = get_conn()

    row = conn.execute(
        """
        SELECT
            id,
            title,
            ai_summary
        FROM news
        WHERE id=?
        """,
        (
            news_id,
        )
    ).fetchone()

    if not row:

        conn.close()

        return False

    # 已分析过
    if row["ai_summary"]:

        conn.close()

        return True

    try:

        start = time.time()

        result = analyze_news(
            row["title"]
        )

        data = _parse_ai_result(
            result
        )

        _save_ai_result(
            conn,
            news_id,
            data
        )

        conn.commit()

        print(
            f"AI分析完成: "
            f"{row['title']} "
            f"耗时 {time.time() - start:.1f}s"
        )

        conn.close()

        return True

    except Exception as e:

        print(
            "AI分析失败:",
            e
        )

        conn.close()

        return False


def analyze_unprocessed_news(
    limit=20
):

    conn = get_conn()

    rows = conn.execute(
        """
        SELECT
            id,
            title
        FROM news
        WHERE ai_summary IS NULL
           OR ai_summary=''
        LIMIT ?
        """,
        (
            limit,
        )
    ).fetchall()

    success = 0

    for row in rows:

        try:

            start = time.time()

            result = analyze_news(
                row["title"]
            )

            data = _parse_ai_result(
                result
            )

            _save_ai_result(
                conn,
                row["id"],
                data
            )

            success += 1

            print(
                f"AI分析完成: "
                f"{row['title']} "
                f"耗时 {time.time() - start:.1f}s"
            )

        except Exception as e:

            print(
                "AI分析失败:",
                row["title"],
                e
            )

    conn.commit()

    conn.close()

    return success