from __future__ import annotations

import sqlite3
from pathlib import Path


DB_PATH = Path("knowledge") / "knowledge.db"


def search_posts(query: str, limit: int = 10) -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    words = [w.strip().lower() for w in query.split() if len(w.strip()) >= 3]

    if not words:
        return []

    where = " OR ".join(["LOWER(text) LIKE ?" for _ in words])
    params = [f"%{w}%" for w in words]

    sql = f"""
        SELECT
            channel,
            message_id,
            date,
            text,
            views,
            forwards,
            link,
            topics
        FROM posts
        WHERE {where}
        ORDER BY views DESC
        LIMIT ?
    """

    rows = conn.execute(sql, params + [limit]).fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_top_posts(limit: int = 10) -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    rows = conn.execute("""
        SELECT
            channel,
            message_id,
            date,
            text,
            views,
            forwards,
            link,
            topics
        FROM posts
        WHERE views IS NOT NULL
        ORDER BY views DESC
        LIMIT ?
    """, (limit,)).fetchall()

    conn.close()
    return [dict(row) for row in rows]


def get_topic_posts(topic: str, limit: int = 10) -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    rows = conn.execute("""
        SELECT
            channel,
            message_id,
            date,
            text,
            views,
            forwards,
            link,
            topics
        FROM posts
        WHERE LOWER(topics) LIKE LOWER(?)
        ORDER BY views DESC
        LIMIT ?
    """, (f"%{topic}%", limit)).fetchall()

    conn.close()
    return [dict(row) for row in rows]


def get_channel_profile(channel: str) -> dict | None:
    import json

    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("""
        SELECT profile_json
        FROM channel_profiles
        WHERE channel = ?
    """, (channel,)).fetchone()

    conn.close()

    if not row:
        return None

    return json.loads(row[0])