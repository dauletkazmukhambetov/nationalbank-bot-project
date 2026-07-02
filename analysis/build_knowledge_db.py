from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pandas as pd


BASE_DIR = Path("knowledge")
ANALYSIS_DIR = BASE_DIR / "analysis"
DB_PATH = BASE_DIR / "knowledge.db"

CHANNELS = {
    "tengenomika": BASE_DIR / "tengenomika" / "posts.csv",
    "economykz": BASE_DIR / "economykz" / "posts.csv",
    "economic_basics": BASE_DIR / "economic_basics" / "posts.csv",
}


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def create_tables(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel TEXT,
            message_id INTEGER,
            date TEXT,
            text TEXT,
            views INTEGER,
            forwards INTEGER,
            media TEXT,
            link TEXT,
            text_length INTEGER,
            emoji_count INTEGER,
            has_hashtag INTEGER,
            has_link INTEGER,
            topics TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS channel_profiles (
            channel TEXT PRIMARY KEY,
            profile_json TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS global_topics (
            topic TEXT PRIMARY KEY,
            count INTEGER
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS style_words (
            word TEXT PRIMARY KEY,
            count INTEGER
        )
    """)

    conn.commit()


def insert_posts(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute("DELETE FROM posts")

    for channel, path in CHANNELS.items():
        analyzed_path = ANALYSIS_DIR / f"{channel}_posts_analyzed.csv"

        if analyzed_path.exists():
            df = pd.read_csv(analyzed_path)
        elif path.exists():
            df = pd.read_csv(path)
        else:
            print(f"⚠️ Нет файла: {path}")
            continue

        for _, row in df.iterrows():
            cur.execute("""
                INSERT INTO posts (
                    channel, message_id, date, text, views, forwards,
                    media, link, text_length, emoji_count,
                    has_hashtag, has_link, topics
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                channel,
                int(row.get("id", 0)) if pd.notna(row.get("id", None)) else None,
                str(row.get("date", "")),
                str(row.get("text", "")),
                int(row.get("views", 0)) if pd.notna(row.get("views", None)) else None,
                int(row.get("forwards", 0)) if pd.notna(row.get("forwards", None)) else None,
                str(row.get("media", "")),
                str(row.get("link", "")),
                int(row.get("text_length", 0)) if pd.notna(row.get("text_length", None)) else None,
                int(row.get("emoji_count", 0)) if pd.notna(row.get("emoji_count", None)) else None,
                int(bool(row.get("has_hashtag", False))),
                int(bool(row.get("has_link", False))),
                str(row.get("topics", "")),
            ))

    conn.commit()


def insert_profiles(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute("DELETE FROM channel_profiles")

    profiles = load_json(ANALYSIS_DIR / "channel_profile.json")

    for channel, profile in profiles.items():
        cur.execute("""
            INSERT INTO channel_profiles (channel, profile_json)
            VALUES (?, ?)
        """, (
            channel,
            json.dumps(profile, ensure_ascii=False),
        ))

    conn.commit()


def insert_topics(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute("DELETE FROM global_topics")

    topics = load_json(ANALYSIS_DIR / "topics.json")

    for topic, count in topics.items():
        cur.execute("""
            INSERT INTO global_topics (topic, count)
            VALUES (?, ?)
        """, (topic, int(count)))

    conn.commit()


def insert_style_words(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute("DELETE FROM style_words")

    words = load_json(ANALYSIS_DIR / "style_dictionary.json")

    for word, count in words.items():
        cur.execute("""
            INSERT INTO style_words (word, count)
            VALUES (?, ?)
        """, (word, int(count)))

    conn.commit()


def main() -> None:
    BASE_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)

    create_tables(conn)
    insert_posts(conn)
    insert_profiles(conn)
    insert_topics(conn)
    insert_style_words(conn)

    conn.close()

    print("✅ База знаний создана")
    print(f"📁 Файл: {DB_PATH}")


if __name__ == "__main__":
    main()