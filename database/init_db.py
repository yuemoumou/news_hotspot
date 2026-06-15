import sqlite3

conn = sqlite3.connect("news.db")

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS news(
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    title TEXT NOT NULL,

    summary TEXT,

    url TEXT UNIQUE,

    source TEXT,

    publish_time DATETIME,

    crawl_time DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()
conn.close()