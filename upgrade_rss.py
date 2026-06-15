# upgrade_rss.py

import sqlite3

conn = sqlite3.connect(
    "news.db"
)

try:

    conn.execute("""
    ALTER TABLE sites
    ADD COLUMN site_type
    TEXT DEFAULT 'spider'
    """)

    print(
        "site_type添加成功"
    )

except Exception as e:

    print(e)

conn.commit()
conn.close()