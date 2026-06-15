"""
趋势分析服务（升级版）
- 使用共享分词器和停用词
- 热点关键词提取
- 关键词趋势分析（24h / 7d / 30d）
"""
import pandas as pd
from collections import Counter
from database.db import get_conn
from services.aggregation_service import cut_words


def get_hot_keywords(days=7):
    """
    获取热点关键词
    返回: list of (word, count)
    """
    conn = get_conn()

    rows = conn.execute("""
        SELECT title
        FROM news
        WHERE crawl_time >= datetime('now', ?)
          AND title IS NOT NULL
          AND title <> ''
    """, (f'-{days} day',)).fetchall()
    conn.close()

    words = []
    for row in rows:
        words.extend(cut_words(row["title"]))

    counter = Counter(words)
    return counter.most_common(20)


def keyword_trend(keyword, mode="hour"):
    """
    关键词趋势分析
    mode: "hour" | "7day" | "30day"
    返回: DataFrame with columns ["time", "count"]
    """
    conn = get_conn()

    if mode == "hour":
        df = pd.read_sql_query("""
            SELECT
                strftime('%Y-%m-%d %H:00', crawl_time) AS time,
                title
            FROM news
            WHERE crawl_time >= datetime('now', '-24 hour')
        """, conn)
    elif mode == "7day":
        df = pd.read_sql_query("""
            SELECT
                date(crawl_time) AS time,
                title
            FROM news
            WHERE crawl_time >= datetime('now', '-7 day')
        """, conn)
    else:
        df = pd.read_sql_query("""
            SELECT
                date(crawl_time) AS time,
                title
            FROM news
            WHERE crawl_time >= datetime('now', '-30 day')
        """, conn)

    conn.close()

    if df.empty:
        return pd.DataFrame(columns=["time", "count"])

    result = []
    for t in sorted(df["time"].unique()):
        count = len(
            df[
                (df["time"] == t) &
                (df["title"].str.contains(keyword, na=False))
            ]
        )
        result.append({"time": t, "count": count})

    return pd.DataFrame(result)
