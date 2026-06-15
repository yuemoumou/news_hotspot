"""
新闻聚合服务
- Jieba 分词 + 自定义词典 + 停用词
- TF-IDF 关键词提取
- 热点事件聚类
- 新闻关联推荐
"""
import os
import math
import jieba
import pandas as pd
from collections import Counter, defaultdict
from database.db import get_conn

# ============================================================
# 加载自定义词典和停用词
# ============================================================

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 加载自定义词典
_userdict_path = os.path.join(_BASE_DIR, "database", "userdict.txt")
if os.path.exists(_userdict_path):
    jieba.load_userdict(_userdict_path)

# 加载停用词
_stopwords_path = os.path.join(_BASE_DIR, "database", "stopwords.txt")
STOP_WORDS = set()
if os.path.exists(_stopwords_path):
    with open(_stopwords_path, "r", encoding="utf-8") as f:
        for line in f:
            word = line.strip()
            if word and not word.startswith("//"):
                STOP_WORDS.add(word)

# 补充默认停用词
STOP_WORDS.update({
    "的", "了", "和", "是", "在", "将", "与", "对", "中", "为",
    "及", "有", "一个", "我们", "他们"
})


def cut_words(text):
    """Jieba 分词，过滤停用词和单字"""
    if not text:
        return []
    words = []
    for word in jieba.cut(text):
        word = word.strip()
        if len(word) < 2:
            continue
        if word in STOP_WORDS:
            continue
        # 过滤纯数字、纯标点
        if word.isdigit():
            continue
        words.append(word)
    return words


# ============================================================
# TF-IDF 关键词提取
# ============================================================

def _compute_tfidf(documents):
    """
    对文档列表计算 TF-IDF
    documents: list of list of words
    返回: list of list of (word, tfidf_score)
    """
    N = len(documents)
    if N == 0:
        return []

    # 计算 DF (document frequency)
    df = defaultdict(int)
    for doc in documents:
        unique_words = set(doc)
        for word in unique_words:
            df[word] += 1

    # 计算 IDF
    idf = {}
    for word, count in df.items():
        idf[word] = math.log((N + 1) / (count + 1)) + 1

    # 计算每个文档的 TF-IDF
    results = []
    for doc in documents:
        tf = Counter(doc)
        total = sum(tf.values()) or 1
        scores = []
        for word, count in tf.items():
            score = (count / total) * idf.get(word, 0)
            scores.append((word, score))
        scores.sort(key=lambda x: x[1], reverse=True)
        results.append(scores)
    return results


# ============================================================
# 热点关键词统计
# ============================================================

def get_hot_keywords_aggregated(days=7, limit=30):
    """
    获取热点关键词（聚合版）
    - 取最近 N 天标题
    - Jieba 分词
    - TF-IDF 计算权重
    - 返回 top N 关键词及其权重
    """
    conn = get_conn()
    rows = conn.execute("""
        SELECT id, title
        FROM news
        WHERE crawl_time >= datetime('now', ?)
          AND title IS NOT NULL
          AND title <> ''
    """, (f'-{days} day',)).fetchall()
    conn.close()

    if not rows:
        return []

    # 分词
    docs = []
    doc_ids = []
    for row in rows:
        words = cut_words(row["title"])
        if words:
            docs.append(words)
            doc_ids.append(row["id"])

    if not docs:
        return []

    # TF-IDF
    tfidf_results = _compute_tfidf(docs)

    # 汇总每个词的总权重
    word_total_weight = defaultdict(float)
    word_doc_count = defaultdict(int)
    for scores in tfidf_results:
        seen = set()
        for word, score in scores[:10]:  # 每篇取 top10 关键词
            word_total_weight[word] += score
            if word not in seen:
                word_doc_count[word] += 1
                seen.add(word)

    # 排序：综合权重 × 文档覆盖度
    hot_list = []
    for word, total_weight in word_total_weight.items():
        doc_cnt = word_doc_count.get(word, 1)
        combined_score = total_weight * math.log(doc_cnt + 1)
        hot_list.append({
            "keyword": word,
            "score": round(combined_score, 4),
            "count": doc_cnt
        })

    hot_list.sort(key=lambda x: x["score"], reverse=True)
    return hot_list[:limit]


# ============================================================
# 热点事件聚合
# ============================================================

def aggregate_hot_events(days=3, min_news=3, max_events=12):
    """
    聚合热点事件（类似 Google News）
    1. 取最近 N 天新闻
    2. 提取每篇新闻的关键词
    3. 按核心关键词分组
    4. 返回事件列表，每个事件包含相关新闻
    """
    conn = get_conn()
    rows = conn.execute("""
        SELECT id, title, url, source, crawl_time, ai_summary, category, keywords
        FROM news
        WHERE crawl_time >= datetime('now', ?)
          AND title IS NOT NULL
          AND title <> ''
          AND source IS NOT NULL
          AND source <> ''
        ORDER BY crawl_time DESC
    """, (f'-{days} day',)).fetchall()
    conn.close()

    if not rows:
        return []

    # 为每篇新闻提取核心关键词（取 TF-IDF 最高的 3 个）
    all_docs = []
    for row in rows:
        words = cut_words(row["title"])
        all_docs.append(words)

    tfidf_results = _compute_tfidf(all_docs)

    news_with_keywords = []
    for i, row in enumerate(rows):
        top_keywords = [w for w, s in tfidf_results[i][:5]] if i < len(tfidf_results) else []
        news_with_keywords.append({
            "id": row["id"],
            "title": row["title"],
            "url": row["url"],
            "source": row["source"],
            "crawl_time": row["crawl_time"],
            "ai_summary": row["ai_summary"],
            "category": row["category"],
            "keywords": row["keywords"],
            "core_words": top_keywords[:3]  # 最多 3 个核心词
        })

    # 按核心关键词聚合
    # 策略：以第一个核心关键词为事件簇的锚点
    event_clusters = {}  # keyword -> list of news indices

    for i, item in enumerate(news_with_keywords):
        core = item["core_words"]
        if not core:
            continue
        # 使用第一个（权重最高）核心词作为聚类锚点
        anchor = core[0]
        if anchor not in event_clusters:
            event_clusters[anchor] = []
        event_clusters[anchor].append(i)

    # 合并重叠的簇（两个簇如果有 >50% 新闻重叠就合并）
    # 简化版：只保留有足够新闻的簇
    events = []
    for keyword, indices in event_clusters.items():
        if len(indices) < min_news:
            continue
        # 去重（一篇新闻可能属于多个簇，按首次出现归入）
        event_news = [news_with_keywords[i] for i in indices]
        # 按来源去重（同一来源取最新一篇）
        seen_sources = set()
        unique_news = []
        for n in event_news:
            if n["source"] not in seen_sources:
                unique_news.append(n)
                seen_sources.add(n["source"])

        events.append({
            "event_keyword": keyword,
            "news_count": len(indices),
            "source_count": len(unique_news),
            "news_list": unique_news[:15],  # 每个事件最多展示 15 篇
            "sources": list(seen_sources)
        })

    # 按新闻数量排序
    events.sort(key=lambda x: x["news_count"], reverse=True)
    return events[:max_events]


# ============================================================
# 相关新闻推荐
# ============================================================

def recommend_related_news(news_id, limit=8):
    """
    基于关键词相似度推荐相关新闻
    - 提取目标新闻关键词
    - 计算与其他新闻的关键词重叠度
    - 返回最相关的 N 篇
    """
    conn = get_conn()

    # 获取目标新闻
    target = conn.execute("""
        SELECT id, title, keywords, category
        FROM news
        WHERE id = ?
    """, (news_id,)).fetchone()

    if not target:
        conn.close()
        return []

    # 提取目标关键词
    target_words = set()
    if target["keywords"]:
        target_words.update(w.strip() for w in target["keywords"].split(",") if w.strip())
    if target["title"]:
        target_words.update(cut_words(target["title"]))
    if target["category"]:
        target_words.add(target["category"])

    if not target_words:
        conn.close()
        return []

    # 候选新闻（同分类 + 最近30天）
    candidates = conn.execute("""
        SELECT id, title, url, source, crawl_time, keywords, category, ai_summary
        FROM news
        WHERE id != ?
          AND crawl_time >= datetime('now', '-30 day')
        ORDER BY crawl_time DESC
        LIMIT 500
    """, (news_id,)).fetchall()
    conn.close()

    if not candidates:
        return []

    # 计算相似度
    scored = []
    for row in candidates:
        cand_words = set()
        if row["keywords"]:
            cand_words.update(w.strip() for w in row["keywords"].split(",") if w.strip())
        if row["title"]:
            cand_words.update(cut_words(row["title"]))
        if row["category"]:
            cand_words.add(row["category"])

        if not cand_words:
            continue

        # Jaccard 相似度
        intersection = len(target_words & cand_words)
        union = len(target_words | cand_words)
        similarity = intersection / union if union > 0 else 0

        # 同分类加分
        if target["category"] and row["category"] == target["category"]:
            similarity += 0.2

        if similarity > 0:
            scored.append((similarity, dict(row)))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored[:limit]]


# ============================================================
# 全局热词云数据
# ============================================================

def get_wordcloud_data(days=7, limit=100):
    """返回词云所需的 (word, weight) 列表"""
    keywords = get_hot_keywords_aggregated(days=days, limit=limit)
    return [(k["keyword"], k["score"]) for k in keywords]


# ============================================================
# 事件详情：获取某关键词的全部相关新闻
# ============================================================

def get_event_news(keyword, days=7):
    """获取某热点关键词的全部相关新闻"""
    conn = get_conn()
    rows = conn.execute("""
        SELECT id, title, url, source, crawl_time, ai_summary, category, keywords
        FROM news
        WHERE crawl_time >= datetime('now', ?)
          AND title IS NOT NULL
        ORDER BY crawl_time DESC
        LIMIT 500
    """, (f'-{days} day',)).fetchall()
    conn.close()

    # 过滤：标题包含关键词
    matched = []
    for row in rows:
        if keyword.lower() in (row["title"] or "").lower():
            matched.append(dict(row))
        elif row["keywords"] and keyword in (row["keywords"] or ""):
            matched.append(dict(row))

    return matched
