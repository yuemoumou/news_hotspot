# check_ai.py

import sqlite3

conn = sqlite3.connect("news.db")

rows = conn.execute("""
SELECT
title,
ai_summary,
category,
keywords,
sentiment_label
FROM news
WHERE ai_summary IS NOT NULL
LIMIT 5
""").fetchall()

for row in rows:
    print(row)

conn.close()