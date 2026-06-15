# check_unknown_news.py

import sqlite3

conn = sqlite3.connect("news.db")

rows = conn.execute("""
SELECT
    title,
    url
FROM news
WHERE source IS NULL
OR source=''
LIMIT 20
""").fetchall()

for row in rows:
    print(row)

conn.close()