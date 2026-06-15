import sqlite3

conn = sqlite3.connect(
    "news.db"
)

rows = conn.execute("""
PRAGMA table_info(news)
""").fetchall()

for row in rows:
    print(row)

conn.close()