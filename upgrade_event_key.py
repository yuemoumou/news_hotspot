from database.db import get_conn

conn = get_conn()

columns = [
    row[1]
    for row in conn.execute(
        "PRAGMA table_info(news)"
    ).fetchall()
]

if "event_key" not in columns:

    conn.execute(
        """
        ALTER TABLE news
        ADD COLUMN event_key TEXT
        """
    )

    conn.commit()

    print("event_key 添加成功")

else:

    print("event_key 已存在")

conn.close()