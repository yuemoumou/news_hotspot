"""
热点分析服务（升级版）
- 使用共享词典和停用词
- Jieba 分词 + TF-IDF
- 热点关键词 Top10/20/50
- 多维度统计
"""
from collections import Counter
from database.db import get_conn
from services.aggregation_service import cut_words, get_hot_keywords_aggregated


def get_hot_keywords(limit=20):
    """
    获取热点关键词（兼容旧接口，使用新分词逻辑）
    """
    keywords = get_hot_keywords_aggregated(days=30, limit=limit)
    return [(k["keyword"], k["count"]) for k in keywords]


def get_hot_keywords_with_score(limit=20, days=7):
    """获取带权重的热点关键词"""
    return get_hot_keywords_aggregated(days=days, limit=limit)


def get_source_stats():
    """获取来源统计"""
    conn = get_conn()
    rows = conn.execute("""
        SELECT source, COUNT(*) as count
        FROM news
        WHERE source IS NOT NULL AND source <> ''
        GROUP BY source
        ORDER BY count DESC
    """).fetchall()
    conn.close()
    return [(r["source"], r["count"]) for r in rows]


def get_daily_stats(days=30):
    """获取每日新闻统计"""
    conn = get_conn()
    rows = conn.execute("""
        SELECT date(crawl_time) as day, COUNT(*) as count
        FROM news
        WHERE crawl_time >= datetime('now', ?)
        GROUP BY day
        ORDER BY day
    """, (f'-{days} day',)).fetchall()
    conn.close()
    return [(r["day"], r["count"]) for r in rows]


def get_hourly_stats(days=30):
    """获取每小时新闻分布"""
    conn = get_conn()
    rows = conn.execute("""
        SELECT strftime('%H', crawl_time) as hour, COUNT(*) as count
        FROM news
        WHERE crawl_time >= datetime('now', ?)
        GROUP BY hour
        ORDER BY hour
    """, (f'-{days} day',)).fetchall()
    conn.close()
    return [(r["hour"], r["count"]) for r in rows]
