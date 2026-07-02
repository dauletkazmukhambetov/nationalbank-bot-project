from dataclasses import dataclass


@dataclass
class PostResult:

    title: str

    text: str

    hashtags: list[str]

    source: str

    quality_score: float