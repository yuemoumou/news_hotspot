"""
热点趋势分析页面（升级版）
- 热词趋势对比（多词同图）
- 24小时趋势
- 7天/30天趋势
- Plotly 交互图表
- 热词排行榜
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from services.trend_service import (
    get_hot_keywords,
    keyword_trend
)

st.title("📊 热点趋势分析")

# ============================================================
# 模式选择
# ============================================================

mode = st.radio(
    "统计粒度",
    ["最近 24 小时", "最近 7 天", "最近 30 天"],
    horizontal=True
)

if mode == "最近 24 小时":
    trend_mode = "hour"
    days_for_hot = 1
    title_suffix = "（24小时）"
elif mode == "最近 7 天":
    trend_mode = "7day"
    days_for_hot = 7
    title_suffix = "（7天）"
else:
    trend_mode = "30day"
    days_for_hot = 30
    title_suffix = "（30天）"

# ============================================================
# 热词排行榜 TOP 20
# ============================================================

hot_words = get_hot_keywords(days=days_for_hot)

if not hot_words:
    st.warning("暂无数据")
    st.stop()

df_hot = pd.DataFrame(hot_words, columns=["关键词", "次数"])

st.subheader(f"🔥 热门关键词 TOP 20 {title_suffix}")

col_a, col_b = st.columns([3, 2])

with col_a:
    # 树状图（Treemap）展示关键词权重
    fig_treemap = px.treemap(
        df_hot.head(20),
        path=["关键词"],
        values="次数",
        title="热点关键词分布",
        color="次数",
        color_continuous_scale="reds"
    )
    fig_treemap.update_layout(height=400)
    st.plotly_chart(fig_treemap, use_container_width=True)

with col_b:
    # 横向柱状图
    df_sorted = df_hot.head(20).sort_values("次数", ascending=True)
    fig_bar = px.bar(
        df_sorted,
        y="关键词",
        x="次数",
        orientation="h",
        title="关键词频次排名",
        color="次数",
        color_continuous_scale="blues",
        text="次数"
    )
    fig_bar.update_traces(textposition="outside")
    fig_bar.update_layout(height=400, yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig_bar, use_container_width=True)

st.divider()

# ============================================================
# 关键词趋势对比
# ============================================================

st.subheader("📈 关键词趋势对比")

col1, col2 = st.columns([1, 3])

with col1:
    hot_word_list = df_hot["关键词"].tolist()
    selected_words = st.multiselect(
        "选择对比关键词",
        hot_word_list,
        default=hot_word_list[:3] if len(hot_word_list) >= 3 else hot_word_list,
        key="compare_words"
    )

    # 快捷选择
    st.caption("💡 提示：可多选关键词进行趋势对比")

with col2:
    if selected_words:
        # 构建多词趋势图
        fig_multi = go.Figure()
        colors = px.colors.qualitative.Set2

        for i, word in enumerate(selected_words):
            df_trend = keyword_trend(word, mode=trend_mode)
            if not df_trend.empty:
                color = colors[i % len(colors)]
                fig_multi.add_trace(go.Scatter(
                    x=df_trend["time"],
                    y=df_trend["count"],
                    name=word,
                    mode="lines+markers",
                    line=dict(color=color, width=2),
                    marker=dict(size=6),
                    hovertemplate=f"<b>{word}</b><br>时间: %{{x}}<br>次数: %{{y}}<extra></extra>"
                ))

        fig_multi.update_layout(
            title=f"关键词趋势对比{title_suffix}",
            xaxis_title="时间" if trend_mode != "hour" else "小时",
            yaxis_title="出现次数",
            height=450,
            hovermode="x unified",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        st.plotly_chart(fig_multi, use_container_width=True)

        # 汇总表格
        st.subheader("趋势数据表格")
        all_trends = {}
        for word in selected_words:
            df_t = keyword_trend(word, mode=trend_mode)
            if not df_t.empty:
                all_trends[word] = df_t

        if all_trends:
            # 合并展示
            tabs = st.tabs(selected_words)
            for i, (word, df_t) in enumerate(all_trends.items()):
                with tabs[i]:
                    df_display = df_t.rename(columns={"time": "时间", "count": "次数"})
                    st.dataframe(df_display, use_container_width=True, hide_index=True)
                    total = df_t["count"].sum()
                    st.caption(f"**{word}** 在统计周期内共出现 **{total}** 次")
    else:
        st.info("请选择至少一个关键词查看趋势")

st.divider()

# ============================================================
# 热力图：关键词 × 时间
# ============================================================

st.subheader("🗺️ 关键词热度热力图")

top_words_for_heat = hot_word_list[:10]

if top_words_for_heat:
    heat_data = []
    for word in top_words_for_heat:
        df_t = keyword_trend(word, mode=trend_mode)
        if not df_t.empty:
            for _, row in df_t.iterrows():
                heat_data.append({
                    "关键词": word,
                    "时间": row["time"],
                    "次数": row["count"]
                })

    if heat_data:
        df_heat = pd.DataFrame(heat_data)
        df_pivot = df_heat.pivot_table(
            index="关键词",
            columns="时间",
            values="次数",
            fill_value=0
        )

        fig_heat = px.imshow(
            df_pivot,
            title=f"关键词 × 时间 热度分布{title_suffix}",
            labels=dict(x="时间", y="关键词", color="次数"),
            color_continuous_scale="YlOrRd",
            aspect="auto"
        )
        fig_heat.update_layout(height=350)
        st.plotly_chart(fig_heat, use_container_width=True)
