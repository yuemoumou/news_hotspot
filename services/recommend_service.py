"""
新闻推荐服务
- 基于 TF-IDF 相似度推荐
- 基于关键词匹配推荐
- 基于协同分类推荐
- 热门新闻推荐
"""
from database.db import get_conn
from services.aggregation_service import cut_words


def get_hot_news(limit=20, days=7):
    """
    获取热门新闻（基于多维度热度评分）
    热度 = AI已分析加分 + 有分类加分 + 最近抓取
    """
    conn = get_conn()
    rows = conn.execute("""
        SELECT id, title, url, source, crawl_time, ai_summary, category, keywords
        FROM news
        WHERE crawl_time >= datetime('now', ?)
        ORDER BY
            (CASE WHEN ai_summary IS NOT NULL AND ai_summary <> '' THEN 3 ELSE 0 END) +
            (CASE WHEN category IS NOT NULL AND category <> '' THEN 2 ELSE 0 END) +
            (CASE WHEN keywords IS NOT NULL AND keywords <> '' THEN 1 ELSE 0 END)
            DESC,
            crawl_time DESC
        LIMIT ?
    """, (f'-{days} day', limit)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def recommend_by_category(category, exclude_id=None, limit=10):
    """基于分类推荐"""
    conn = get_conn()
    params = [category]
    exclude_clause = ""
    if exclude_id:
        exclude_clause = "AND id != ?"
        params.append(exclude_id)

    rows = conn.execute(f"""
        SELECT id, title, url, source, crawl_time, ai_summary, category, keywords
        FROM news
        WHERE category = ?
          {exclude_clause}
        ORDER BY crawl_time DESC
        LIMIT ?
    """, params + [limit]).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def recommend_trending_keywords(limit=15):
    """推荐热门关键词（用于发现页）"""
    from services.aggregation_service import get_hot_keywords_aggregated
    return get_hot_keywords_aggregated(days=3, limit=limit)


# ============================================================
# 收藏功能
# ============================================================

def init_favorite_table():
    """创建收藏表"""
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS favorite (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            news_id INTEGER NOT NULL,
            saved_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (news_id) REFERENCES news(id),
            UNIQUE(news_id)
        )
    """)
    conn.commit()
    conn.close()


def add_favorite(news_id):
    """收藏新闻"""
    conn = get_conn()
    try:
        conn.execute("""
            INSERT OR IGNORE INTO favorite (news_id, saved_time)
            VALUES (?, datetime('now', 'localtime'))
        """, (news_id,))
        conn.commit()
        ok = True
    except Exception:
        ok = False
    conn.close()
    return ok


def remove_favorite(news_id):
    """取消收藏"""
    conn = get_conn()
    conn.execute("DELETE FROM favorite WHERE news_id = ?", (news_id,))
    conn.commit()
    conn.close()


def is_favorited(news_id):
    """检查是否已收藏"""
    conn = get_conn()
    row = conn.execute("SELECT 1 FROM favorite WHERE news_id = ?", (news_id,)).fetchone()
    conn.close()
    return row is not None


def get_favorites(limit=100):
    """获取收藏列表"""
    conn = get_conn()
    rows = conn.execute("""
        SELECT n.*, f.saved_time as fav_time
        FROM news n
        JOIN favorite f ON n.id = f.news_id
        ORDER BY f.saved_time DESC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ============================================================
# 阅读历史
# ============================================================

def init_history_table():
    """创建阅读历史表"""
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            news_id INTEGER NOT NULL,
            viewed_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (news_id) REFERENCES news(id)
        )
    """)
    conn.commit()
    conn.close()


def record_view(news_id):
    """记录浏览"""
    conn = get_conn()
    conn.execute("""
        INSERT INTO history (news_id, viewed_time)
        VALUES (?, datetime('now', 'localtime'))
    """, (news_id,))
    conn.commit()
    conn.close()


def get_history(limit=100):
    """获取浏览历史（去重，取最新）"""
    conn = get_conn()
    rows = conn.execute("""
        SELECT DISTINCT n.*, h.viewed_time
        FROM news n
        JOIN (
            SELECT news_id, MAX(viewed_time) as viewed_time
            FROM history
            GROUP BY news_id
        ) h ON n.id = h.news_id
        ORDER BY h.viewed_time DESC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def clear_history():
    """清除所有历史"""
    conn = get_conn()
    conn.execute("DELETE FROM history")
    conn.commit()
    conn.close()
