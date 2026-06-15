"""
高级搜索服务
- FTS5 全文检索
- 来源筛选
- 时间筛选
- 分类筛选
- 多维度排序
- 搜索日志记录
"""
from datetime import datetime
from database.db import get_conn


def search_news(
    keyword="",
    source=None,
    days=None,
    category=None,
    sort_by="relevance",
    limit=100
):
    """
    高级搜索
    - keyword: 搜索关键词
    - source: 来源筛选（None 表示全部）
    - days: 时间范围（None 表示不限，1/7/30）
    - category: 分类筛选（None 表示全部）
    - sort_by: "relevance" | "newest" | "hottest"
    - limit: 返回数量上限
    """
    conn = get_conn()

    conditions = []
    params = []

    # --- 关键词搜索 ---
    use_fts = False
    if keyword and keyword.strip():
        use_fts = True
        conditions.append("""
            news.id IN (
                SELECT rowid FROM news_fts WHERE news_fts MATCH ?
            )
        """)
        params.append(keyword.strip())

    # --- 来源筛选 ---
    if source and source != "全部":
        conditions.append("news.source = ?")
        params.append(source)

    # --- 时间筛选 ---
    if days:
        conditions.append("news.crawl_time >= datetime('now', ?)")
        params.append(f'-{days} day')

    # --- 分类筛选 ---
    if category and category != "全部":
        conditions.append("news.category = ?")
        params.append(category)

    # --- 构建 WHERE ---
    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    # --- 排序 ---
    if sort_by == "newest":
        order_clause = "ORDER BY news.crawl_time DESC"
    elif sort_by == "hottest":
        # 热度 = 有 AI 摘要优先 + 最近抓取
        order_clause = "ORDER BY (CASE WHEN news.ai_summary IS NOT NULL AND news.ai_summary <> '' THEN 1 ELSE 0 END) DESC, news.crawl_time DESC"
    else:
        # relevance: 有关键词匹配的优先，再按时间排
        if use_fts:
            order_clause = "ORDER BY news.crawl_time DESC"
        else:
            order_clause = "ORDER BY news.crawl_time DESC"

    # --- 执行查询 ---
    sql = f"""
        SELECT DISTINCT news.*
        FROM news
        {where_clause}
        {order_clause}
        LIMIT ?
    """
    params.append(limit)

    try:
        rows = conn.execute(sql, params).fetchall()
    except Exception as e:
        # FTS 查询失败时回退到 LIKE 搜索
        if use_fts:
            # 重建不含 FTS 的条件
            conditions_no_fts = []
            params_no_fts = []
            if keyword and keyword.strip():
                conditions_no_fts.append("(news.title LIKE ? OR news.keywords LIKE ?)")
                kw_param = f"%{keyword.strip()}%"
                params_no_fts.append(kw_param)
                params_no_fts.append(kw_param)
            if source and source != "全部":
                conditions_no_fts.append("news.source = ?")
                params_no_fts.append(source)
            if days:
                conditions_no_fts.append("news.crawl_time >= datetime('now', ?)")
                params_no_fts.append(f'-{days} day')
            if category and category != "全部":
                conditions_no_fts.append("news.category = ?")
                params_no_fts.append(category)

            where_fallback = "WHERE " + " AND ".join(conditions_no_fts) if conditions_no_fts else ""

            rows = conn.execute(f"""
                SELECT DISTINCT news.*
                FROM news
                {where_fallback}
                {order_clause}
                LIMIT ?
            """, params_no_fts + [limit]).fetchall()
        else:
            raise e

    conn.close()
    return rows


# ============================================================
# 搜索日志
# ============================================================

def init_search_log_table():
    """创建搜索日志表（如果不存在）"""
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS search_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT NOT NULL,
            search_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            result_count INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()


def log_search(keyword, result_count):
    """记录搜索日志"""
    conn = get_conn()
    conn.execute("""
        INSERT INTO search_log (keyword, search_time, result_count)
        VALUES (?, datetime('now', 'localtime'), ?)
    """, (keyword, result_count))
    conn.commit()
    conn.close()


def get_search_log(limit=50):
    """获取搜索日志"""
    conn = get_conn()
    rows = conn.execute("""
        SELECT keyword, search_time, result_count
        FROM search_log
        ORDER BY search_time DESC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return rows


def get_hot_searches(limit=10):
    """获取热门搜索词（去重统计）"""
    conn = get_conn()
    rows = conn.execute("""
        SELECT keyword, COUNT(*) as cnt
        FROM search_log
        WHERE search_time >= datetime('now', '-7 day')
        GROUP BY keyword
        ORDER BY cnt DESC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return rows


def get_available_sources():
    """获取数据库中已有的新闻来源列表"""
    conn = get_conn()
    rows = conn.execute("""
        SELECT DISTINCT source
        FROM news
        WHERE source IS NOT NULL AND source <> ''
        ORDER BY source
    """).fetchall()
    conn.close()
    return [r["source"] for r in rows]


def get_available_categories():
    """获取数据库中已有的分类列表"""
    conn = get_conn()
    rows = conn.execute("""
        SELECT DISTINCT category
        FROM news
        WHERE category IS NOT NULL AND category <> ''
        ORDER BY category
    """).fetchall()
    conn.close()
    return [r["category"] for r in rows]
