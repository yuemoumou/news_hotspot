from database.db import get_conn
from datetime import datetime


def get_sites():

    conn = get_conn()

    rows = conn.execute("""
    SELECT *
    FROM sites
    ORDER BY id
    """).fetchall()

    conn.close()

    return rows


def add_site(
    name,
    url,
    spider,
    site_type
):

    conn = get_conn()

    conn.execute("""
    INSERT INTO sites(
        name,
        url,
        spider,
        site_type
    )
    VALUES(
        ?,?,?,?
    )
    """,
    (
        name,
        url,
        spider,
        site_type
    ))

    conn.commit()

    conn.close()


def delete_site(site_id):

    conn = get_conn()

    conn.execute("""
    DELETE FROM sites
    WHERE id=?
    """,
    (
        site_id,
    ))

    conn.commit()

    conn.close()


def toggle_site(
    site_id,
    enabled
):

    conn = get_conn()

    conn.execute("""
    UPDATE sites
    SET enabled=?
    WHERE id=?
    """,
    (
        enabled,
        site_id
    ))

    conn.commit()

    conn.close()


def update_site_stats():

    conn = get_conn()

    now = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    conn.execute("""
    UPDATE sites
    SET

        last_crawl_time=?,

        crawl_count=
            crawl_count+1

    WHERE enabled=1
    """,
    (
        now,
    ))

    conn.commit()

    conn.close()

