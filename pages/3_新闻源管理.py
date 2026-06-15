import streamlit as st

from services.site_service import *

from services.ai_analyze_service import (
    analyze_unprocessed_news
)
from services.category_service import classify_batch

st.title("⚙ 新闻源管理")

st.subheader("新增新闻源")

name = st.text_input(
    "名称"
)

url = st.text_input(
    "网址"
)

site_type = st.selectbox(

    "新闻源类型",

    [
        "spider",
        "rss"
    ]

)

if site_type == "spider":

    spider = st.text_input(
        "Spider函数名"
    )

else:

    spider = ""

if st.button(
    "添加新闻源"
):

    add_site(
        name,
        url,
        spider,
        site_type
    )

    st.success(
        "添加成功"
    )

    st.rerun()

st.divider()

st.subheader(
    "已有新闻源"
)

rows = get_sites()

for row in rows:

    c1, c2, c3, c4, c5, c6 = st.columns(
        [2, 4, 2, 2, 1, 1]
    )

    c1.write(
        row["name"]
    )

    c2.write(
        row["url"]
    )

    c3.write(
        row["site_type"]
    )

    status = bool(
        row["enabled"]
    )

    if c4.checkbox(
        "启用",
        value=status,
        key=f"site_{row['id']}"
    ) != status:

        toggle_site(
            row["id"],
            not status
        )

        st.rerun()

    if c6.button(
        "删除",
        key=f"del_{row['id']}"
    ):

        delete_site(
            row["id"]
        )

        st.rerun()

st.divider()

st.subheader(
    "🤖 AI分析 & 分类"
)

limit = st.number_input(
    "处理新闻数量",
    min_value=1,
    max_value=100,
    value=20
)

ai_col1, ai_col2 = st.columns(2)

with ai_col1:
    if st.button(
        "开始AI分析",
        use_container_width=True
    ):

        with st.spinner(
            "DeepSeek分析中..."
        ):

            count = analyze_unprocessed_news(
                limit
            )

        st.success(
            f"完成 {count} 条新闻分析"
        )

with ai_col2:
    if st.button(
        "📂 规则批量分类",
        use_container_width=True
    ):

        with st.spinner(
            "规则分类中..."
        ):

            count = classify_batch(
                limit
            )

        st.success(
            f"完成 {count} 条规则分类"
        )