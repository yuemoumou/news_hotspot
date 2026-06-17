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

# 导入数据（显式指定 rowid = news.id，保证搜索时行号一致）
cursor.execute("""
INSERT INTO news_fts(rowid, title, source, url)
SELECT id, title, source, url
FROM news
""")

conn.commit()

count = cursor.execute(
    "SELECT COUNT(*) FROM news_fts"
).fetchone()[0]

print("FTS记录数:", count)

conn.close()