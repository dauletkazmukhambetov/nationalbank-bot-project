import json
from pathlib import Path
from typing import Any

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "indicators.json"


def load_indicators() -> list[dict[str, Any]]:
    with DATA_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def get_sections(indicators: list[dict[str, Any]]) -> list[str]:
    return sorted({item["section"] for item in indicators})


def by_section(indicators: list[dict[str, Any]], section: str) -> list[dict[str, Any]]:
    return [item for item in indicators if item["section"] == section]


def get_indicator(indicators: list[dict[str, Any]], indicator_id: str) -> dict[str, Any] | None:
    for item in indicators:
        if str(item["id"]) == str(indicator_id):
            return item
    return None
