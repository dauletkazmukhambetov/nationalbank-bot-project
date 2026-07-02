from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent.parent))

from analysis.economic_analyzer import analyze_dataframe
from models.prompt_context import PromptContext
from services.knowledge_search import get_channel_profile, search_posts


def build_prompt_context(
    indicator_name: str,
    year: int,
    df: pd.DataFrame,
    channel: str = "tengenomika",
    report_metadata: dict[str, Any] | None = None,
) -> PromptContext:
    analysis = analyze_dataframe(
        df=df,
        title=indicator_name,
    )

    related_posts = search_posts(
        query=indicator_name,
        limit=5,
    )

    channel_style = get_channel_profile(channel) or {}

    return PromptContext(
        indicator=indicator_name,
        year=year,
        analysis=analysis,
        related_posts=related_posts,
        channel_style=channel_style,
        report_metadata=report_metadata or {},
        audience="Аудитория экономического Telegram-канала",
        language="ru",
        tone="аналитический",
        max_length=1800,
    )


def context_to_prompt(context: PromptContext) -> str:
    related_texts = []

    for i, post in enumerate(context.related_posts, start=1):
        text = str(post.get("text", "")).strip()
        if len(text) > 700:
            text = text[:700] + "..."

        related_texts.append(
            f"{i}. Канал: {post.get('channel')}\n"
            f"Просмотры: {post.get('views')}\n"
            f"Текст: {text}"
        )

    related_block = "\n\n".join(related_texts) if related_texts else "Похожих публикаций не найдено."

    return f"""
Ты — экономический редактор Telegram-канала.

Задача:
на основе отчёта и анализа данных подготовить пост для Telegram.

Показатель:
{context.indicator}

Период:
{context.year}

Анализ данных:
{context.analysis}

Профиль канала:
{context.channel_style}

Похожие публикации:
{related_block}

Требования к тексту:
- язык: русский;
- стиль: аналитический, но понятный широкой аудитории;
- не выдумывать факты, которых нет в анализе;
- обязательно использовать цифры из анализа;
- объяснить, что изменилось;
- сделать краткий вывод;
- длина до {context.max_length} символов;
- не копировать похожие публикации дословно.

Верни только готовый текст поста.
""".strip()