"""
高级新闻搜索页面
- 全文搜索
- 来源筛选
- 时间筛选
- 分类筛选
- 多维度排序
- 搜索日志
- 热门搜索
"""
import streamlit as st
import pandas as pd
from datetime import datetime

from services.search_service import (
    search_news,
    init_search_log_table,
    log_search,
    get_search_log,
    get_hot_searches,
    get_available_sources,
    get_available_categories
)

# 初始化搜索日志表
init_search_log_table()

st.title("🔍 高级新闻搜索")

# ============================================================
# 搜索栏
# ============================================================

search_col1, search_col2 = st.columns([4, 1])

with search_col1:
    keyword = st.text_input(
        "搜索关键词",
        placeholder="输入关键词搜索新闻...",
        label_visibility="collapsed"
    )

with search_col2:
    search_clicked = st.button("🔍 搜索", use_container_width=True, type="primary")

# ============================================================
# 高级筛选
# ============================================================

with st.expander("📋 高级筛选", expanded=False):
    filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)

    with filter_col1:
        # 来源筛选
        sources = get_available_sources()
        source_options = ["全部"] + sources
        selected_source = st.selectbox("新闻来源", source_options, key="filter_source")

    with filter_col2:
        # 时间筛选
        time_options = {
            "全部时间": None,
            "最近 1 天": 1,
            "最近 7 天": 7,
            "最近 30 天": 30
        }
        selected_time_label = st.selectbox("时间范围", list(time_options.keys()), index=2)
        selected_days = time_options[selected_time_label]

    with filter_col3:
        # 分类筛选
        categories = get_available_categories()
        category_options = ["全部"] + categories
        selected_category = st.selectbox("新闻分类", category_options, key="filter_category")

    with filter_col4:
        # 排序方式
        sort_options = {
            "相关度优先": "relevance",
            "最新优先": "newest",
            "最热优先": "hottest"
        }
        selected_sort_label = st.selectbox("排序方式", list(sort_options.keys()))
        selected_sort = sort_options[selected_sort_label]

# ============================================================
# 热门搜索
# ============================================================

hot_searches = get_hot_searches(limit=8)
if hot_searches:
    st.caption("🔥 热门搜索：")
    hot_cols = st.columns(min(len(hot_searches), 8))
    for i, (kw, cnt) in enumerate(hot_searches):
        with hot_cols[i]:
            if st.button(f"{kw}", key=f"hot_{kw}", use_container_width=True):
                keyword = kw
                st.rerun()

# ============================================================
# 执行搜索
# ============================================================

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

        # --- 结果统计 ---
        if rows:
            st.success(f"找到 {len(rows)} 条结果")

            # 来源统计
            from collections import Counter
            source_dist = Counter(r["source"] for r in rows)
            source_text = " | ".join(f"{s}({c})" for s, c in source_dist.most_common(6))
            st.caption(f"📡 来源分布：{source_text}")

            st.divider()

            # --- 结果列表 ---
            for row in rows:
                col_title, col_actions = st.columns([5, 1])

                with col_title:
                    st.markdown(f"### [{row['title']}]({row['url']})")

                with col_actions:
                    # 相关推荐按钮
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

            # --- 推荐面板 ---
            if "recommend_for" in st.session_state and st.session_state["recommend_for"]:
                rec_id = st.session_state["recommend_for"]
                st.sidebar.subheader("🔗 相关推荐")
                from services.aggregation_service import recommend_related_news
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

# ============================================================
# 搜索日志
# ============================================================

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
