"""
新闻聚合页面
- 今日热点事件（类似 Google News）
- 热点关键词云
- 相关新闻聚合
- 来源统计
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from collections import Counter

from services.aggregation_service import (
    get_hot_keywords_aggregated,
    aggregate_hot_events,
    get_event_news,
    recommend_related_news
)

st.set_page_config(page_title="新闻聚合", page_icon="📰", layout="wide")

st.title("📰 新闻聚合")

# ============================================================
# 顶部控制栏
# ============================================================

col1, col2, col3 = st.columns([2, 2, 1])
with col1:
    days = st.selectbox("统计时间范围", [1, 3, 7, 14, 30], index=2, key="agg_days")
with col2:
    min_news = st.slider("最少相关新闻数", 2, 10, 3, key="min_news")
with col3:
    st.metric("时间范围", f"最近 {days} 天")

st.divider()

# ============================================================
# 热点关键词 TOP 20
# ============================================================

st.subheader("🔥 热点关键词 TOP 20")

hot_keywords = get_hot_keywords_aggregated(days=days, limit=20)

if hot_keywords:
    df_kw = pd.DataFrame(hot_keywords)

    col_a, col_b = st.columns([3, 2])

    with col_a:
        fig = px.bar(
            df_kw.head(20),
            x="keyword",
            y="score",
            color="count",
            title="热点关键词权重",
            labels={"keyword": "关键词", "score": "权重", "count": "出现篇数"},
            color_continuous_scale="reds"
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.subheader("关键词权重表")
        st.dataframe(
            df_kw.rename(columns={
                "keyword": "关键词",
                "score": "权重分数",
                "count": "相关篇数"
            }),
            use_container_width=True,
            height=400,
            hide_index=True
        )

    # 词频展示
    st.caption("💡 提示：点击下方关键词可查看相关新闻")
    selected_kw = st.selectbox(
        "选择一个关键词查看详情",
        ["—"] + [k["keyword"] for k in hot_keywords]
    )

    if selected_kw and selected_kw != "—":
        st.divider()
        st.subheader(f"📌 「{selected_kw}」相关新闻")

        related = get_event_news(selected_kw, days=days)
        if related:
            st.success(f"共找到 {len(related)} 篇相关新闻")
            source_counts = Counter(r["source"] for r in related)
            st.caption(f"来源分布：{' | '.join(f'{s}({c})' for s, c in source_counts.most_common())}")

            for item in related[:20]:
                col_title, col_source = st.columns([5, 1])
                with col_title:
                    st.markdown(f"**[{item['title']}]({item['url']})**")
                with col_source:
                    st.caption(item["source"])
                if item.get("ai_summary"):
                    st.info(f"🤖 {item['ai_summary']}")
                if item.get("keywords"):
                    st.caption(f"🏷️ {item['keywords']}")
                st.divider()
        else:
            st.warning("暂无相关新闻")
else:
    st.warning("暂无热点数据，请先抓取新闻")

st.divider()

# ============================================================
# 热点事件聚合（Google News 风格）
# ============================================================

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
            expanded=(i < 3)  # 前 3 个默认展开
        ):
            # 来源统计徽章
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

# ============================================================
# 新闻推荐（基于选中新闻）
# ============================================================

st.subheader("🔗 新闻关联推荐")

from database.db import get_conn

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
        ["—"] + list(news_options.keys())
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
