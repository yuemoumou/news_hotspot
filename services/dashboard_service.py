from database.db import get_conn


def get_dashboard_data():

    conn = get_conn()

    total_news = conn.execute("""
    SELECT COUNT(*)
    FROM news
    """).fetchone()[0]

    today_news = conn.execute("""
    SELECT COUNT(*)
    FROM news
    WHERE date(crawl_time)=date('now')
    """).fetchone()[0]

    site_count = conn.execute("""
    SELECT COUNT(*)
    FROM sites
    WHERE enabled=1
    """).fetchone()[0]

    sites = conn.execute("""
    SELECT
        name,
        crawl_count,
        last_crawl_time,
        enabled
    FROM sites
    ORDER BY id
    """).fetchall()

    conn.close()

    return {
        "total_news": total_news,
        "today_news": today_news,
        "site_count": site_count,
        "sites": sites
    }