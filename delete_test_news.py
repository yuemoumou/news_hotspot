# delete_test_news.py

import sqlite3

conn = sqlite3.connect("news.db")

conn.execute("""
DELETE FROM news
WHERE id=1140
""")

conn.commit()

conn.close()

print("删除完成")