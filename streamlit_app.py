import streamlit as st
import pandas as pd

# 必须放最前面
st.set_page_config(
    page_title="智能新闻热点聚合系统",
    page_icon="📰",
    layout="wide"
)

from database.db import get_conn
from services.scheduler_service import crawl_job
from services.dashboard_service import get_dashboard_data
from services.recommend_service import (
    init_favorite_table,
    init_history_table,
    add_favorite,
    remove_favorite,
    is_favorited,
    record_view,
    get_hot_news
)
from services.ai_analyze_service import (
    analyze_one_news
)

# 初始化收藏和历史表
init_favorite_table()
init_history_table()

st.title("📰 智能新闻热点聚合系统")

conn = get_conn()

total_news = conn.execute("""
SELECT COUNT(*)
FROM news
""").fetchone()[0]

ai_news = conn.execute("""
SELECT COUNT(*)
FROM news
WHERE ai_summary IS NOT NULL
AND ai_summary <> ''
""").fetchone()[0]

conn.close()

col1, col2 = st.columns(2)

with col1:

    st.metric(
        "新闻总数",
        total_news
    )

with col2:

    st.metric(
        "AI已分析",
        ai_news
    )

# =====================
# 手动刷新按钮
# =====================

if st.button("🔄 立即抓取新闻"):

    with st.spinner("正在抓取新闻..."):

        crawl_job()

    st.success(
        "抓取完成"
    )

    st.rerun()

# =====================
# Dashboard数据
# =====================

dashboard = get_dashboard_data()

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "新闻总数",
    dashboard["total_news"]
)

c2.metric(
    "今日新增",
    dashboard["today_news"]
)

c3.metric(
    "新闻源",
    dashboard["site_count"]
)

# 最近24小时新增

conn = get_conn()

latest_24h = conn.execute("""
SELECT COUNT(*)
FROM news
WHERE crawl_time >= datetime(
    'now',
    '-24 hour'
)
""").fetchone()[0]

c4.metric(
    "24小时新增",
    latest_24h
)

st.divider()

# =====================
# 新闻源状态
# =====================

st.subheader("📡 新闻源状态")

for site in dashboard["sites"]:

    name = site["name"]

    enabled = site["enabled"]

    crawl_count = site["crawl_count"]

    last_time = site["last_crawl_time"]

    status = "🟢运行中" if enabled else "🔴已禁用"

    st.write(
        f"""
{name}

状态：{status}

抓取次数：{crawl_count}

最后抓取时间：{last_time}
"""
    )

st.divider()

# =====================
# 🔥 今日热点事件
# =====================

st.subheader("🔥 今日热点事件")

from services.aggregation_service import aggregate_hot_events, get_hot_keywords_aggregated

hot_events = aggregate_hot_events(days=1, min_news=2, max_events=8)
hot_kws = get_hot_keywords_aggregated(days=1, limit=10)

if hot_events:
    event_cols = st.columns(min(len(hot_events), 4))
    for i, event in enumerate(hot_events[:8]):
        with event_cols[i % 4]:
            with st.container(border=True):
                st.markdown(f"### {event['event_keyword']}")
                st.caption(f"📰 {event['news_count']} 篇相关新闻")
                st.caption(f"📡 {event['source_count']} 个来源")
                for item in event["news_list"][:3]:
                    st.markdown(f"- [{item['title'][:40]}...]({item['url']})" if len(item['title']) > 40 else f"- [{item['title']}]({item['url']})")
else:
    st.info("暂无热点事件数据")

st.divider()

# =====================
# 🏷️ 今日热词
# =====================

if hot_kws:
    st.subheader("🏷️ 今日热词")
    kw_html = " ".join(
        f'<span style="display:inline-block;background:#ff4b4b;color:white;padding:4px 12px;margin:4px;border-radius:16px;font-size:{max(12, min(22, 12 + int(k["score"]*2)))}px">{k["keyword"]}</span>'
        for k in hot_kws[:15]
    )
    st.markdown(kw_html, unsafe_allow_html=True)
    st.divider()

# =====================
# 🔥 热门新闻
# =====================

hot_news_list = get_hot_news(limit=10, days=7)
if hot_news_list:
    st.subheader("🔥 热门新闻")
    hot_cols = st.columns(min(len(hot_news_list), 5))
    for i, hn in enumerate(hot_news_list[:10]):
        with hot_cols[i % 5]:
            st.markdown(f"[{hn['title'][:45]}...]({hn['url']})" if len(hn['title']) > 45 else f"[{hn['title']}]({hn['url']})")
            st.caption(f"{hn['source'] or ''} | {hn['category'] or ''}")
    st.divider()

# =====================
# 最新新闻
# =====================

st.subheader("📰 最新新闻")

rows = conn.execute("""
SELECT *
FROM news
ORDER BY id DESC
LIMIT 100
""").fetchall()

for row in rows:

    col1, col2, col3 = st.columns(
        [7, 1, 1]
    )

    with col1:

        st.markdown(
            f"### [{row['title']}]({row['url']})"
        )

    with col2:
        # 收藏按钮
        fav = is_favorited(row["id"])
        if fav:
            if st.button("⭐", key=f"fav_{row['id']}", help="取消收藏"):
                remove_favorite(row["id"])
                st.rerun()
        else:
            if st.button("☆", key=f"fav_{row['id']}", help="收藏"):
                add_favorite(row["id"])
                # 记录浏览
                record_view(row["id"])
                st.rerun()

    with col3:

        if not row["ai_summary"]:

            if st.button(
                "🤖",
                key=f"ai_{row['id']}",
                help="AI分析"
            ):

                with st.spinner(
                    "AI分析中..."
                ):

                    ok = analyze_one_news(
                        row["id"]
                    )

                if ok:

                    st.success(
                        "完成"
                    )

                    st.rerun()

                else:

                    st.error(
                        "失败"
                    )

        else:

            st.caption("✅")

    source = row["source"] or "未知来源"

    crawl_time = row["crawl_time"] or ""

    st.caption(
        f"{source} | {crawl_time}"
    )

    summary = row["ai_summary"]

    if summary:

        st.info(
            f"🤖 {summary}"
        )

    category = row["category"]

    if category:

        st.caption(
            f"📂 分类：{category}"
        )

    keywords = row["keywords"]

    if keywords:

        st.caption(
            f"🏷️ 关键词：{keywords}"
        )

    label = row["sentiment_label"]

    if label:

        if label == "正面":

            st.success(
                f"😊 {label}"
            )

        elif label == "负面":

            st.error(
                f"😞 {label}"
            )

        else:

            st.warning(
                f"😐 {label}"
            )

    st.divider()

# =====================
# 新闻来源统计
# =====================

st.subheader("📈 新闻来源统计")

df = pd.read_sql_query("""
SELECT
    source,
    COUNT(*) AS count
FROM news
WHERE
    source IS NOT NULL
    AND TRIM(source) <> ''
GROUP BY source
ORDER BY count DESC
""", conn)

if not df.empty:

    st.dataframe(
        df,
        use_container_width=True
    )

    st.bar_chart(
        df.set_index(
            "source"
        )
    )