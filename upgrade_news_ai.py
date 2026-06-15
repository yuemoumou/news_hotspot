# upgrade_news_ai.py

import sqlite3

conn = sqlite3.connect("news.db")

try:
    conn.execute("""
    ALTER TABLE news
    ADD COLUMN ai_summary TEXT
    """)
except:
    pass

try:
    conn.execute("""
    ALTER TABLE news
    ADD COLUMN sentiment REAL
    """)
except:
    pass

conn.commit()

print("升级完成")

conn.close()