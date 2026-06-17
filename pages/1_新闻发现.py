"""
新闻发现页面（整合版）
- Tab 1: 高级新闻搜索（全文搜索、筛选、排序、搜索日志）
- Tab 2: 热点事件聚合（Google News 风格事件聚类、关联推荐）
"""
import streamlit as st
import pandas as pd
from datetime import datetime
from collections import Counter

from services.search_service import (
    search_news,
    init_search_log_table,
    log_search,
    get_search_log,
    get_hot_searches,
    get_available_sources,
    get_available_categories
)
from services.aggregation_service import (
    aggregate_hot_events,
    recommend_related_news
)
from services.recommend_service import (
    record_view,
    init_history_table,
    add_favorite,
    remove_favorite,
    is_favorited
)
from database.db import get_conn

# 初始化搜索日志表
init_search_log_table()
# 初始化历史表
init_history_table()

st.set_page_config(page_title="新闻发现", page_icon="🔍", layout="wide")

st.title("🔍 新闻发现")

# ============================================================
# 标签页切换
# ============================================================

tab_search, tab_events = st.tabs(["🔍 新闻搜索", "📰 热点事件"])

# ============================================================
# Tab 1: 新闻搜索（来自 1_新闻搜索.py）
# ============================================================

with tab_search:
    # --- 搜索栏 ---
    search_col1, search_col2 = st.columns([4, 1])

    with search_col1:
        keyword = st.text_input(
            "搜索关键词",
            placeholder="输入关键词搜索新闻...",
            label_visibility="collapsed",
            key="search_keyword"
        )

    with search_col2:
        search_clicked = st.button("🔍 搜索", use_container_width=True, type="primary", key="search_btn")

    # --- 高级筛选 ---
    with st.expander("📋 高级筛选", expanded=False):
        filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)

        with filter_col1:
            sources = get_available_sources()
            source_options = ["全部"] + sources
            selected_source = st.selectbox("新闻来源", source_options, key="filter_source")

        with filter_col2:
            time_options = {
                "全部时间": None,
                "最近 1 天": 1,
                "最近 7 天": 7,
                "最近 30 天": 30
            }
            selected_time_label = st.selectbox("时间范围", list(time_options.keys()), index=2)
            selected_days = time_options[selected_time_label]

        with filter_col3:
            categories = get_available_categories()
            category_options = ["全部"] + categories
            selected_category = st.selectbox("新闻分类", category_options, key="filter_category")

        with filter_col4:
            sort_options = {
                "相关度优先": "relevance",
                "最新优先": "newest",
                "最热优先": "hottest"
            }
            selected_sort_label = st.selectbox("排序方式", list(sort_options.keys()))
            selected_sort = sort_options[selected_sort_label]

    # --- 执行搜索 ---
    if keyword or search_clicked:
        if keyword and keyword.strip():
            with st.spinner("搜索中..."):
                rows = search_news(
                    keyword=keyword.strip(),
                    source=selected_source if selected_source != "全部" else None,
                    days=selected_days,
                    category=selected_category if selected_category != "全部" else None,
                    sort_by=selected_sort,
                    limit=200
                )

                # 记录搜索日志
                log_search(keyword.strip(), len(rows))

            # 结果统计
            if rows:
                st.success(f"找到 {len(rows)} 条结果")

                source_dist = Counter(r["source"] for r in rows)
                source_text = " | ".join(f"{s}({c})" for s, c in source_dist.most_common(6))
                st.caption(f"📡 来源分布：{source_text}")

                st.divider()

                # 结果列表
                for row in rows:
                    # 记录浏览
                    record_view(row["id"])

                    col_title, col_actions = st.columns([5, 1])

                    with col_title:
                        st.markdown(f"### [{row['title']}]({row['url']})")

                    with col_actions:
                        if st.button("🔗 推荐", key=f"rec_{row['id']}"):
                            st.session_state["recommend_for"] = row["id"]
                            st.rerun()

                    # 元信息
                    meta_parts = []
                    if row["source"]:
                        meta_parts.append(f"📡 {row['source']}")
                    if row["crawl_time"]:
                        meta_parts.append(f"🕐 {row['crawl_time']}")
                    if row["category"]:
                        meta_parts.append(f"📂 {row['category']}")
                    st.caption(" | ".join(meta_parts))

                    # AI 摘要
                    if row["ai_summary"]:
                        st.info(f"🤖 {row['ai_summary']}")

                    # 关键词
                    if row["keywords"]:
                        kw_list = [k.strip() for k in row["keywords"].split(",") if k.strip()]
                        kw_html = " ".join(
                            f'<span style="display:inline-block;background:#eee;padding:2px 8px;margin:2px;border-radius:10px;font-size:12px">{k}</span>'
                            for k in kw_list[:8]
                        )
                        st.markdown(kw_html, unsafe_allow_html=True)

                    # 情感标签
                    if row["sentiment_label"]:
                        if row["sentiment_label"] == "正面":
                            st.success(f"😊 {row['sentiment_label']}")
                        elif row["sentiment_label"] == "负面":
                            st.error(f"😞 {row['sentiment_label']}")
                        else:
                            st.warning(f"😐 {row['sentiment_label']}")

                    st.divider()

                # 推荐面板（侧边栏）
                if "recommend_for" in st.session_state and st.session_state["recommend_for"]:
                    rec_id = st.session_state["recommend_for"]
                    st.sidebar.subheader("🔗 相关推荐")
                    recs = recommend_related_news(rec_id, limit=6)
                    if recs:
                        for rec in recs:
                            st.sidebar.markdown(f"- [{rec['title'][:50]}]({rec['url']})")
                            st.sidebar.caption(f"  {rec['source'] or ''}")
                    else:
                        st.sidebar.caption("暂无推荐")
                    if st.sidebar.button("关闭推荐"):
                        st.session_state["recommend_for"] = None
                        st.rerun()

            else:
                st.warning("未找到相关结果，请尝试其他关键词")

        else:
            st.info("请输入搜索关键词")

    # --- 搜索日志 ---
    with st.expander("📝 搜索日志", expanded=False):
        log_col1, log_col2 = st.columns(2)

        with log_col1:
            st.subheader("最近搜索")
            logs = get_search_log(limit=30)
            if logs:
                df_log = pd.DataFrame(logs, columns=["搜索词", "搜索时间", "结果数"])
                st.dataframe(df_log, use_container_width=True, hide_index=True)
            else:
                st.caption("暂无搜索记录")

        with log_col2:
            st.subheader("热门搜索词")
            hot_s = get_hot_searches(limit=15)
            if hot_s:
                df_hot_s = pd.DataFrame(hot_s, columns=["搜索词", "搜索次数"])
                st.bar_chart(df_hot_s.set_index("搜索词"))
            else:
                st.caption("暂无搜索统计")

# ============================================================
# Tab 2: 热点事件（来自 5_新闻聚合.py，去掉关键词排名部分）
# ============================================================

with tab_events:
    # --- 控制栏 ---
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        days = st.selectbox("统计时间范围", [1, 3, 7, 14, 30], index=2, key="agg_days")
    with col2:
        min_news = st.slider("最少相关新闻数", 2, 10, 3, key="min_news")
    with col3:
        st.metric("时间范围", f"最近 {days} 天")

    st.divider()

    # --- 热点事件聚合（Google News 风格）---
    st.subheader("📰 热点事件聚合")

    events = aggregate_hot_events(days=days, min_news=min_news, max_events=15)

    if events:
        st.success(f"共聚合 {len(events)} 个热点事件")

        for i, event in enumerate(events):
            keyword = event["event_keyword"]
            news_count = event["news_count"]
            source_count = event["source_count"]
            sources_str = "、".join(event["sources"][:5])

            with st.expander(
                f"🔥 **{keyword}** — 相关新闻 {news_count} 篇 | {source_count} 个来源 | {sources_str}",
                expanded=(i < 3)
            ):
                source_badges = " | ".join(
                    f"**{s}**" for s in event["sources"][:8]
                )
                st.caption(f"📡 覆盖来源：{source_badges}")

                for item in event["news_list"][:10]:
                    col_news, col_source = st.columns([5, 1])
                    with col_news:
                        st.markdown(f"- [{item['title']}]({item['url']})")
                    with col_source:
                        st.caption(item["source"])
                    if item.get("ai_summary"):
                        st.info(f"  🤖 {item['ai_summary']}")

                if news_count > len(event["news_list"]):
                    st.caption(f"... 还有 {news_count - len(event['news_list'])} 篇相关新闻")

        st.divider()
    else:
        st.info("暂无足够数据聚合事件，请调整时间范围或最少新闻数")

    # --- 新闻关联推荐 ---
    st.subheader("🔗 新闻关联推荐")

    conn = get_conn()
    recent_news = conn.execute("""
        SELECT id, title, source
        FROM news
        WHERE crawl_time >= datetime('now', '-7 day')
        ORDER BY crawl_time DESC
        LIMIT 100
    """).fetchall()
    conn.close()

    if recent_news:
        news_options = {f"[{r['id']}] {r['title'][:60]}": r["id"] for r in recent_news}
        selected_news_label = st.selectbox(
            "选择一篇新闻，查看相关推荐",
            ["—"] + list(news_options.keys()),
            key="rec_select"
        )

        if selected_news_label and selected_news_label != "—":
            selected_id = news_options[selected_news_label]
            recommendations = recommend_related_news(selected_id, limit=8)

            if recommendations:
                st.success(f"为您推荐 {len(recommendations)} 篇相关新闻")
                for rec in recommendations:
                    st.markdown(f"**[{rec['title']}]({rec['url']})**")
                    st.caption(f"来源：{rec['source']} | 分类：{rec.get('category', '—')} | 关键词：{rec.get('keywords', '—')}")
                    if rec.get("ai_summary"):
                        st.info(f"🤖 {rec['ai_summary']}")
                    st.divider()
            else:
                st.info("暂无相关推荐")
    else:
        st.info("新闻数量不足，无法进行推荐")
