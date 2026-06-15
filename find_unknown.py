# find_unknown.py

import sqlite3

conn = sqlite3.connect("news.db")

rows = conn.execute("""
SELECT
    id,
    title,
    url,
    source
FROM news
WHERE source='未知来源'
""").fetchall()

for row in rows:
    print(row)

conn.close()