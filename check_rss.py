# check_rss.py

import sqlite3

conn = sqlite3.connect(
    "news.db"
)

rows = conn.execute("""
SELECT
    source,
    title
FROM news
WHERE source='BBC RSS'
LIMIT 10
""").fetchall()

for row in rows:
    print(row)

conn.close()