from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

import pandas as pd


BASE_DIR = Path("knowledge")
OUTPUT_DIR = BASE_DIR / "analysis"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


CHANNELS = {
    "tengenomika": BASE_DIR / "tengenomika" / "posts.csv",
    "economykz": BASE_DIR / "economykz" / "posts.csv",
    "economic_basics": BASE_DIR / "economic_basics" / "posts.csv",
}


TOPIC_KEYWORDS = {
    "инфляция": ["инфляц", "цены", "индекс потребительских цен", "ипц"],
    "валюта": ["доллар", "курс", "тенге", "валют", "обменник", "usd", "eur", "rub"],
    "нефть": ["нефть", "brent", "opec", "опек"],
    "депозиты": ["депозит", "вклад"],
    "кредиты": ["кредит", "займ", "ипотек"],
    "банки": ["банк", "банковск", "бву"],
    "нацбанк": ["нацбанк", "нб рк", "национальный банк"],
    "нацфонд": ["нацфонд", "национальный фонд"],
    "инвестиции": ["инвестиц", "пии", "капитал"],
    "платежный баланс": ["платежный баланс", "экспорт", "импорт", "счет текущих операций"],
    "азс и топливо": ["бензин", "аи-92", "аи-95", "дизель", "топливо", "азс"],
    "бюджет": ["бюджет", "налог", "расход", "доход"],
    "ввп": ["ввп", "экономический рост", "рост экономики"],
}


STOP_WORDS = {
    "это", "как", "что", "для", "или", "при", "над", "под", "его", "она", "они",
    "уже", "еще", "так", "же", "бы", "по", "на", "из", "в", "и", "с", "к", "о",
    "от", "до", "за", "но", "не", "мы", "вы", "он", "ее", "их", "а", "то", "во",
    "со", "об", "про", "год", "года", "году", "млн", "млрд", "тенге", "казахстан",
    "https", "http", "www", "com", "html", "tengenomika", "economykz",
"telegram", "канал", "ссылка", "подписка", "подписаться"
}


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", str(text).lower()).strip()


def count_emojis(text: str) -> int:
    return len(re.findall(r"[\U0001F300-\U0001FAFF]", str(text)))


import pymorphy3

morph = pymorphy3.MorphAnalyzer()


def remove_markdown_and_links(text: str) -> str:
    text = str(text)

    # убираем ссылки
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"www\.\S+", " ", text)
    text = re.sub(r"t\.me/\S+", " ", text)

    # markdown-ссылки [текст](ссылка) -> текст
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)

    # markdown-символы
    text = text.replace("*", " ")
    text = text.replace("_", " ")
    text = text.replace("`", " ")

    # названия каналов и технические слова
    garbage = [
        "tengenomika",
        "economykz",
        "economic",
        "basics",
        "telegram",
        "канал",
        "подписаться",
    ]

    for word in garbage:
        text = re.sub(word, " ", text, flags=re.IGNORECASE)

    return re.sub(r"\s+", " ", text).strip()


def normalize_word(word: str) -> str:
    word = word.lower().replace("ё", "е")
    parsed = morph.parse(word)

    if not parsed:
        return word

    return parsed[0].normal_form


def extract_words(text: str) -> list[str]:
    text = remove_markdown_and_links(text)
    words = re.findall(r"[а-яa-zA-ZёЁ]{4,}", clean_text(text))

    result = []

    for word in words:
        normal = normalize_word(word)

        if normal in STOP_WORDS:
            continue

        if len(normal) < 4:
            continue

        result.append(normal)

    return result


def detect_topics(text: str) -> list[str]:
    text_norm = clean_text(text)
    found = []

    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(keyword in text_norm for keyword in keywords):
            found.append(topic)

    return found or ["прочее"]


def analyze_channel(name: str, path: Path) -> dict:
    df = pd.read_csv(path)

    if "text" not in df.columns:
        raise ValueError(f"В файле {path} нет колонки text")

    df["text"] = df["text"].fillna("").astype(str)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    df["text_length"] = df["text"].str.len()
    df["emoji_count"] = df["text"].map(count_emojis)
    df["has_hashtag"] = df["text"].str.contains("#", na=False)
    df["has_link"] = df["text"].str.contains("http|t.me|www", case=False, regex=True, na=False)
    df["topics"] = df["text"].map(detect_topics)

    all_words = []
    for text in df["text"]:
        all_words.extend(extract_words(text))

    topic_counter = Counter()
    for topics in df["topics"]:
        topic_counter.update(topics)

    posts_by_date = (
        df.dropna(subset=["date"])
        .assign(day=lambda x: x["date"].dt.date)
        .groupby("day")
        .size()
    )

    profile = {
        "channel": name,
        "posts_count": int(len(df)),
        "average_text_length": round(float(df["text_length"].mean()), 1),
        "median_text_length": round(float(df["text_length"].median()), 1),
        "max_text_length": int(df["text_length"].max()),
        "emoji_posts_share": round(float((df["emoji_count"] > 0).mean()), 3),
        "hashtag_posts_share": round(float(df["has_hashtag"].mean()), 3),
        "link_posts_share": round(float(df["has_link"].mean()), 3),
        "average_views": round(float(pd.to_numeric(df.get("views"), errors="coerce").mean()), 1)
        if "views" in df.columns else None,
        "average_forwards": round(float(pd.to_numeric(df.get("forwards"), errors="coerce").mean()), 1)
        if "forwards" in df.columns else None,
        "posts_per_active_day": round(float(posts_by_date.mean()), 2) if len(posts_by_date) else 0,
        "top_topics": dict(topic_counter.most_common(15)),
        "top_words": dict(Counter(all_words).most_common(50)),
    }

    df.to_csv(OUTPUT_DIR / f"{name}_posts_analyzed.csv", index=False, encoding="utf-8-sig")

    return profile


def main() -> None:
    profiles = {}

    for name, path in CHANNELS.items():
        if not path.exists():
            print(f"⚠️ Нет файла: {path}")
            continue

        print(f"🔍 Анализирую {name}...")
        profiles[name] = analyze_channel(name, path)

    with open(OUTPUT_DIR / "channel_profile.json", "w", encoding="utf-8") as f:
        json.dump(profiles, f, ensure_ascii=False, indent=2)

    all_topics = Counter()
    all_words = Counter()

    for profile in profiles.values():
        all_topics.update(profile["top_topics"])
        all_words.update(profile["top_words"])

    with open(OUTPUT_DIR / "topics.json", "w", encoding="utf-8") as f:
        json.dump(dict(all_topics.most_common()), f, ensure_ascii=False, indent=2)

    with open(OUTPUT_DIR / "style_dictionary.json", "w", encoding="utf-8") as f:
        json.dump(dict(all_words.most_common(100)), f, ensure_ascii=False, indent=2)

    print("✅ Анализ завершён")
    print(f"📁 Результаты сохранены в {OUTPUT_DIR}")


if __name__ == "__main__":
    main()