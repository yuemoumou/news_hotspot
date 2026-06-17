"""
我的收藏页面
- 收藏列表查看
- 取消收藏
- 关联推荐
"""
import streamlit as st
import pandas as pd

from services.recommend_service import (
    init_favorite_table,
    get_favorites,
    remove_favorite,
    is_favorited
)
from services.aggregation_service import recommend_related_news

# 初始化表
init_favorite_table()

st.title("⭐ 我的收藏")

favorites = get_favorites()

if not favorites:
    st.info("暂无收藏。在新闻详情中点击收藏按钮即可添加。")
    st.stop()

st.success(f"共收藏 {len(favorites)} 篇新闻")

# ============================================================
# 收藏列表
# ============================================================

for item in favorites:
    col_main, col_actions = st.columns([6, 1])

    with col_main:
        st.markdown(f"### [{item['title']}]({item['url']})")
        meta = []
        if item.get("source"):
            meta.append(f"📡 {item['source']}")
        if item.get("fav_time"):
            meta.append(f"⭐ 收藏于 {item['fav_time']}")
        if item.get("category"):
            meta.append(f"📂 {item['category']}")
        st.caption(" | ".join(meta))

        if item.get("ai_summary"):
            st.info(f"🤖 {item['ai_summary']}")

        if item.get("keywords"):
            st.caption(f"🏷️ {item['keywords']}")

    with col_actions:
        if st.button("❌ 取消", key=f"unfav_{item['id']}"):
            remove_favorite(item["id"])
            st.rerun()

        # 展开推荐
        with st.expander("🔗 相关推荐"):
            recs = recommend_related_news(item["id"], limit=5)
            if recs:
                for rec in recs:
                    st.markdown(f"- [{rec['title'][:50]}]({rec['url']})")
            else:
                st.caption("暂无推荐")

    st.divider()
