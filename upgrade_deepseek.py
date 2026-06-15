import sqlite3

conn = sqlite3.connect("news.db")

fields = [

    "ai_summary TEXT",

    "category TEXT",

    "keywords TEXT",

    "sentiment_label TEXT"
]

for field in fields:

    try:

        conn.execute(
            f"""
            ALTER TABLE news
            ADD COLUMN {field}
            """
        )

        print(field, "添加成功")

    except:

        print(field, "已存在")

conn.commit()

conn.close()