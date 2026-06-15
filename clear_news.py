from database.db import get_conn

conn = get_conn()

try:

    conn.execute("""
    DELETE FROM news
    """)

    conn.execute("""
    DELETE FROM news_fts
    """)

    conn.commit()

    print("新闻数据已清空")

except Exception as e:

    print(
        "清空失败:",
        e
    )

finally:

    conn.close()