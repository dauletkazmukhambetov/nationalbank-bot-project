import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from services.knowledge_search import (
    search_posts,
    get_top_posts,
    get_topic_posts,
    get_channel_profile,
)


print("\n🔎 Поиск по слову: инфляция")
for post in search_posts("инфляция", limit=5):
    print("-", post["channel"], post["views"], post["text"][:120])


print("\n🔥 Топ постов")
for post in get_top_posts(limit=5):
    print("-", post["channel"], post["views"], post["text"][:120])


print("\n🏷 Посты по теме: валюта")
for post in get_topic_posts("валюта", limit=5):
    print("-", post["channel"], post["views"], post["text"][:120])


print("\n📌 Профиль канала tengenomika")
print(get_channel_profile("tengenomika"))