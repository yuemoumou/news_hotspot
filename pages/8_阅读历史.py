"""
阅读历史页面
- 最近浏览记录
- 浏览记录管理
- 清除历史
"""
import streamlit as st
import pandas as pd

from services.recommend_service import (
    init_history_table,
    get_history,
    clear_history,
    add_favorite,
    remove_favorite,
    is_favorited
)

# 初始化表
init_history_table()

st.title("📖 阅读历史")

# ============================================================
# 操作栏
# ============================================================

col1, col2 = st.columns([3, 1])

with col2:
    if st.button("🗑️ 清除全部历史", type="secondary"):
        clear_history()
        st.rerun()

history = get_history()

if not history:
    st.info("暂无阅读记录。浏览新闻时会自动记录。")
    st.stop()

with col1:
    st.success(f"共 {len(history)} 条浏览记录")

st.divider()

# ============================================================
# 历史列表
# ============================================================

for item in history:
    col_main, col_actions = st.columns([6, 1])

    with col_main:
        st.markdown(f"### [{item['title']}]({item['url']})")
        meta = []
        if item.get("source"):
            meta.append(f"📡 {item['source']}")
        if item.get("viewed_time"):
            meta.append(f"👁 浏览于 {item['viewed_time']}")
        if item.get("category"):
            meta.append(f"📂 {item['category']}")
        st.caption(" | ".join(meta))

        if item.get("ai_summary"):
            st.info(f"🤖 {item['ai_summary']}")

        if item.get("keywords"):
            st.caption(f"🏷️ {item['keywords']}")

    with col_actions:
        # 收藏/取消收藏
        fav = is_favorited(item["id"])
        if fav:
            if st.button("⭐ 已收藏", key=f"unfav_hist_{item['id']}"):
                remove_favorite(item["id"])
                st.rerun()
        else:
            if st.button("☆ 收藏", key=f"fav_hist_{item['id']}"):
                add_favorite(item["id"])
                st.rerun()

    st.divider()
