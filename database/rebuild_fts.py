import sqlite3

conn = sqlite3.connect("news.db")

cursor = conn.cursor()

# 删除旧表
cursor.execute("""
DROP TABLE IF EXISTS news_fts
""")

# 创建FTS5
cursor.execute("""
CREATE VIRTUAL TABLE news_fts
USING fts5(
    title,
    source,
    url
)
""")

# 导入数据
cursor.execute("""
INSERT INTO news_fts(title,source,url)
SELECT title,source,url
FROM news
""")

conn.commit()

count = cursor.execute(
    "SELECT COUNT(*) FROM news_fts"
).fetchone()[0]

print("FTS记录数:", count)

conn.close()