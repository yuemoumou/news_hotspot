"""
热点统计页面（升级版）
- 热点关键词 Top10/Top20/Top50
- Plotly 柱状图/折线图
- 来源统计
- 热词云
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from services.hot_service import (
    get_hot_keywords_with_score,
    get_source_stats,
    get_daily_stats
)

st.title("🔥 热点统计")

# ============================================================
# 控制栏
# ============================================================

col1, col2 = st.columns([2, 1])

with col1:
    days = st.selectbox("统计时间范围", [1, 3, 7, 14, 30], index=2, key="hot_days")

with col2:
    top_n = st.selectbox("显示数量", [10, 20, 50], index=1, key="top_n")

# ============================================================
# 热点关键词
# ============================================================

st.subheader(f"🔥 热点关键词 TOP {top_n}")

hot_data = get_hot_keywords_with_score(limit=top_n, days=days)

if hot_data:
    df_hot = pd.DataFrame(hot_data)

    col_a, col_b = st.columns([2, 1])

    with col_a:
        # 横向柱状图
        df_display = df_hot.head(top_n).sort_values("score", ascending=True)
        fig = px.bar(
            df_display,
            y="keyword",
            x="score",
            orientation="h",
            title=f"热点关键词权重（近 {days} 天）",
            labels={"keyword": "关键词", "score": "权重分数"},
            color="count",
            color_continuous_scale="reds",
            text="count"
        )
        fig.update_traces(
            texttemplate="%{text}篇",
            textposition="outside"
        )
        fig.update_layout(
            height=max(400, top_n * 20),
            yaxis=dict(autorange="reversed")
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.subheader("关键词排名")
        st.dataframe(
            df_hot.rename(columns={
                "keyword": "关键词",
                "score": "权重",
                "count": "出现篇数"
            }).head(top_n),
            use_container_width=True,
            hide_index=True,
            height=400
        )

        # 下载按钮
        csv = df_hot.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📥 下载CSV",
            csv,
            f"hot_keywords_{days}d.csv",
            "text/csv"
        )

else:
    st.warning("暂无数据")

st.divider()

# ============================================================
# 来源统计
# ============================================================

st.subheader("📡 新闻来源统计")

source_data = get_source_stats()

if source_data:
    df_source = pd.DataFrame(source_data, columns=["来源", "数量"])

    col_s1, col_s2 = st.columns(2)

    with col_s1:
        fig_pie = px.pie(
            df_source,
            names="来源",
            values="数量",
            title="来源占比",
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        fig_pie.update_layout(height=350)
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_s2:
        fig_source_bar = px.bar(
            df_source,
            x="来源",
            y="数量",
            title="来源数量对比",
            color="数量",
            color_continuous_scale="blues",
            text="数量"
        )
        fig_source_bar.update_traces(textposition='outside')
        fig_source_bar.update_layout(height=350, coloraxis_showscale=False)
        st.plotly_chart(fig_source_bar, use_container_width=True)

    st.dataframe(df_source, use_container_width=True, hide_index=True)

st.divider()

# ============================================================
# 每日趋势
# ============================================================

st.subheader("📈 每日新闻趋势")

daily_data = get_daily_stats(days=days)

if daily_data:
    df_daily = pd.DataFrame(daily_data, columns=["日期", "数量"])

    fig_line = px.line(
        df_daily,
        x="日期",
        y="数量",
        markers=True,
        title=f"每日新闻数量趋势（近 {days} 天）"
    )
    fig_line.update_layout(height=350)
    st.plotly_chart(fig_line, use_container_width=True)
