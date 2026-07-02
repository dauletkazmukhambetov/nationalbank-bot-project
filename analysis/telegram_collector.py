from __future__ import annotations

import asyncio
import csv
import os
from pathlib import Path

from dotenv import load_dotenv
from telethon import TelegramClient

load_dotenv()

API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")
PHONE = os.getenv("TELEGRAM_PHONE")

CHANNELS = {
    "tengenomika": "https://t.me/tengenomika",
    "economykz": "https://t.me/Economykz_org",
    "economic_basics": "https://t.me/Economic_basics",
}

BASE_DIR = Path("knowledge")


async def collect_channel(
    client: TelegramClient,
    name: str,
    username: str,
    limit: int = 500,
):
    print(f"\n📥 Загружаю {name}...")

    entity = await client.get_entity(username)

    channel_dir = BASE_DIR / name
    images_dir = channel_dir / "images"
    documents_dir = channel_dir / "documents"

    images_dir.mkdir(parents=True, exist_ok=True)
    documents_dir.mkdir(parents=True, exist_ok=True)

    csv_path = channel_dir / "posts.csv"

    rows = []

    async for message in client.iter_messages(entity, limit=limit):
        media_path = ""

        rows.append({
            "id": message.id,
            "date": message.date.isoformat() if message.date else "",
            "text": message.text or "",
            "views": message.views,
            "forwards": message.forwards,
            "media": media_path,
            "link": f"{username}/{message.id}",
        })

    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "id",
                "date",
                "text",
                "views",
                "forwards",
                "media",
                "link",
            ],
        )

        writer.writeheader()
        writer.writerows(rows)

    print(f"✅ {name}: сохранено {len(rows)} постов")


async def main():
    client = TelegramClient(
        "telegram_session",
        API_ID,
        API_HASH,
    )

    await client.start(phone=PHONE)

    for name, username in CHANNELS.items():
        await collect_channel(client, name, username)

    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())