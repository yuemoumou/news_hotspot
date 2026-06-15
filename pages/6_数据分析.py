"""
数据分析中心
- 来源占比分析（饼图）
- 新闻增长趋势（折线图）
- 24小时新闻分布（柱状图）
- 热词趋势分析
- RSS源统计
- 分类统计
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

from database.db import get_conn

st.set_page_config(page_title="数据分析中心", page_icon="📊", layout="wide")

st.title("📊 数据分析中心")

conn = get_conn()

# ============================================================
# 顶部 KPI 卡片
# ============================================================

total = conn.execute("SELECT COUNT(*) FROM news").fetchone()[0]
today = conn.execute("""
    SELECT COUNT(*) FROM news WHERE date(crawl_time) = date('now')
""").fetchone()[0]
yesterday = conn.execute("""
    SELECT COUNT(*) FROM news WHERE date(crawl_time) = date('now', '-1 day')
""").fetchone()[0]
week = conn.execute("""
    SELECT COUNT(*) FROM news WHERE crawl_time >= datetime('now', '-7 day')
""").fetchone()[0]
sources = conn.execute("SELECT COUNT(DISTINCT source) FROM news WHERE source IS NOT NULL AND source <> ''").fetchone()[0]
ai_analyzed = conn.execute("SELECT COUNT(*) FROM news WHERE ai_summary IS NOT NULL AND ai_summary <> ''").fetchone()[0]

kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns(6)
kpi1.metric("新闻总数", total)
kpi2.metric("今日新增", today, delta=f"{today - yesterday}" if yesterday else None)
kpi3.metric("7日新增", week)
kpi4.metric("新闻来源", sources)
kpi5.metric("AI已分析", ai_analyzed)
kpi6.metric("AI覆盖率", f"{ai_analyzed*100//total if total else 0}%")

st.divider()

# ============================================================
# Row 1: 来源占比 + 24小时分布
# ============================================================

row1_col1, row1_col2 = st.columns(2)

with row1_col1:
    st.subheader("📡 新闻来源占比")

    df_source = pd.read_sql_query("""
        SELECT source, COUNT(*) as count
        FROM news
        WHERE source IS NOT NULL AND source <> ''
        GROUP BY source
        ORDER BY count DESC
    """, conn)

    if not df_source.empty:
        # 小来源合并为"其他"
        threshold = df_source["count"].sum() * 0.02  # 2% 以下合并
        df_display = df_source.copy()
        other_mask = df_display["count"] < threshold
        if other_mask.any():
            other_row = pd.DataFrame([{
                "source": "其他",
                "count": df_display.loc[other_mask, "count"].sum()
            }])
            df_display = pd.concat([
                df_display[~other_mask],
                other_row
            ], ignore_index=True)

        fig_pie = px.pie(
            df_display,
            names="source",
            values="count",
            title="新闻来源占比",
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        fig_pie.update_layout(height=400)
        st.plotly_chart(fig_pie, use_container_width=True)

        st.caption("来源明细")
        st.dataframe(
            df_source.rename(columns={"source": "来源", "count": "数量"}),
            use_container_width=True,
            hide_index=True
        )

with row1_col2:
    st.subheader("🕐 24小时新闻分布")

    df_hour = pd.read_sql_query("""
        SELECT strftime('%H', crawl_time) as hour, COUNT(*) as count
        FROM news
        WHERE crawl_time >= datetime('now', '-30 day')
        GROUP BY hour
        ORDER BY hour
    """, conn)

    if not df_hour.empty:
        # 确保 0-23 小时完整
        all_hours = pd.DataFrame({"hour": [f"{h:02d}" for h in range(24)]})
        df_hour_full = all_hours.merge(df_hour, on="hour", how="left").fillna(0)
        df_hour_full["count"] = df_hour_full["count"].astype(int)

        fig_bar = px.bar(
            df_hour_full,
            x="hour",
            y="count",
            title="24小时新闻发布分布（近30天汇总）",
            labels={"hour": "小时", "count": "新闻数量"},
            color="count",
            color_continuous_scale="blues"
        )
        fig_bar.update_layout(height=400, coloraxis_showscale=False)
        st.plotly_chart(fig_bar, use_container_width=True)

        peak_hour = df_hour_full.loc[df_hour_full["count"].idxmax()]
        st.info(f"📊 新闻发布高峰时段：**{peak_hour['hour']}:00**（{int(peak_hour['count'])} 篇）")

st.divider()

# ============================================================
# Row 2: 新闻增长趋势
# ============================================================

st.subheader("📈 新闻增长趋势")

trend_col1, trend_col2 = st.columns([1, 4])

with trend_col1:
    trend_days = st.radio(
        "时间范围",
        [7, 14, 30, 60],
        format_func=lambda d: f"最近 {d} 天",
        index=2,
        horizontal=False,
        key="trend_days"
    )

df_daily = pd.read_sql_query(f"""
    SELECT date(crawl_time) as day, COUNT(*) as count
    FROM news
    WHERE crawl_time >= datetime('now', '-{trend_days} day')
    GROUP BY day
    ORDER BY day
""", conn)

with trend_col2:
    if not df_daily.empty:
        # 计算移动平均
        df_daily["ma7"] = df_daily["count"].rolling(window=7, min_periods=1).mean().round(1)

        fig_trend = go.Figure()
        fig_trend.add_trace(go.Bar(
            x=df_daily["day"],
            y=df_daily["count"],
            name="每日新增",
            marker_color="steelblue"
        ))
        fig_trend.add_trace(go.Scatter(
            x=df_daily["day"],
            y=df_daily["ma7"],
            name="7日均线",
            line=dict(color="red", width=2)
        ))
        fig_trend.update_layout(
            title=f"新闻每日增长趋势（近 {trend_days} 天）",
            xaxis_title="日期",
            yaxis_title="新闻数量",
            height=400,
            hovermode="x unified"
        )
        st.plotly_chart(fig_trend, use_container_width=True)

        # 统计信息
        avg_daily = df_daily["count"].mean()
        max_day = df_daily.loc[df_daily["count"].idxmax()]
        min_day = df_daily.loc[df_daily["count"].idxmin()]

        s1, s2, s3 = st.columns(3)
        s1.metric("日均新增", f"{avg_daily:.1f} 篇")
        s2.metric("最高峰", f"{int(max_day['count'])} 篇", delta=f"{max_day['day']}")
        s3.metric("最低谷", f"{int(min_day['count'])} 篇", delta=f"{min_day['day']}")

st.divider()

# ============================================================
# Row 3: 分类统计 + RSS源统计
# ============================================================

row3_col1, row3_col2 = st.columns(2)

with row3_col1:
    st.subheader("📂 新闻分类统计")

    df_cat = pd.read_sql_query("""
        SELECT category, COUNT(*) as count
        FROM news
        WHERE category IS NOT NULL AND category <> ''
        GROUP BY category
        ORDER BY count DESC
    """, conn)

    if not df_cat.empty:
        fig_cat = px.bar(
            df_cat,
            x="category",
            y="count",
            title="新闻分类数量",
            labels={"category": "分类", "count": "数量"},
            color="count",
            color_continuous_scale="greens",
            text="count"
        )
        fig_cat.update_layout(height=350, coloraxis_showscale=False)
        fig_cat.update_traces(textposition='outside')
        st.plotly_chart(fig_cat, use_container_width=True)

        st.dataframe(
            df_cat.rename(columns={"category": "分类", "count": "数量"}),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("暂无分类数据。请通过 AI 分析或规则分类来标注新闻。")

with row3_col2:
    st.subheader("📡 RSS源统计")

    df_sites = pd.read_sql_query("""
        SELECT
            name,
            site_type,
            enabled,
            crawl_count,
            last_crawl_time
        FROM sites
        ORDER BY crawl_count DESC
    """, conn)

    if not df_sites.empty:
        total_sites = len(df_sites)
        enabled_sites = df_sites["enabled"].sum()
        disabled_sites = total_sites - enabled_sites
        total_crawls = df_sites["crawl_count"].sum()

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("RSS总数", total_sites)
        m2.metric("已启用", int(enabled_sites))
        m3.metric("已停用", int(disabled_sites))
        m4.metric("总抓取次数", int(total_crawls))

        st.dataframe(
            df_sites.rename(columns={
                "name": "名称",
                "site_type": "类型",
                "enabled": "启用",
                "crawl_count": "抓取次数",
                "last_crawl_time": "最后抓取"
            }),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("暂无RSS源数据")

st.divider()

# ============================================================
# Row 4: 热词趋势
# ============================================================

st.subheader("🔥 热词趋势分析")

from services.trend_service import keyword_trend, get_hot_keywords

hot_words = get_hot_keywords(days=7)

if hot_words:
    trend_col1, trend_col2 = st.columns([1, 4])

    hot_word_list = [w for w, _ in hot_words[:20]]

    with trend_col1:
        selected_trend_words = st.multiselect(
            "选择关键词（可多选）",
            hot_word_list,
            default=hot_word_list[:3] if len(hot_word_list) >= 3 else hot_word_list,
            key="trend_words"
        )

    with trend_col2:
        if selected_trend_words:
            fig_multi = go.Figure()
            for word in selected_trend_words:
                df_trend = keyword_trend(word, mode="7day")
                if not df_trend.empty:
                    fig_multi.add_trace(go.Scatter(
                        x=df_trend["time"],
                        y=df_trend["count"],
                        name=word,
                        mode="lines+markers"
                    ))

            fig_multi.update_layout(
                title="关键词趋势对比（近7天）",
                xaxis_title="日期",
                yaxis_title="出现次数",
                height=400,
                hovermode="x unified"
            )
            st.plotly_chart(fig_multi, use_container_width=True)
        else:
            st.info("请选择至少一个关键词")

conn.close()
