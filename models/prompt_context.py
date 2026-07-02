from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PromptContext:
    """
    Полный контекст,
    который будет получать ИИ.
    """

    indicator: str
    year: int

    analysis: dict[str, Any]

    related_posts: list[dict[str, Any]]

    channel_style: dict[str, Any]

    report_metadata: dict[str, Any] = field(default_factory=dict)

    graph_description: str | None = None

    audience: str = "Широкая аудитория"

    language: str = "ru"

    tone: str = "аналитический"

    max_length: int = 1800