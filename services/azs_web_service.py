from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any

import pandas as pd
import requests
from bs4 import BeautifulSoup

from services.local_excel_service import _write_report, _clean_price


AZS_URL = "https://oilclub.kz/prices_azs"

FUEL_COLUMNS = [
    "АИ-92",
    "АИ-92 Prime",
    "АИ-95",
    "АИ-95 Prime",
    "АИ-98",
    "ДТ",
    "ДТЗ",
    "ДТЗ (ПТФ-32)",
    "Газ",
]

AZS_CACHE: tuple[float, pd.DataFrame] | None = None
CACHE_TTL_SECONDS = 300


def _clean_text(value: object) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def _split_semicolon(text: str) -> list[str]:
    return [_clean_text(x) for x in str(text).split(";")]


def fetch_azs_prices() -> pd.DataFrame:
    global AZS_CACHE

    now = time.time()

    if AZS_CACHE is not None:
        cached_time, cached_df = AZS_CACHE
        if now - cached_time < CACHE_TTL_SECONDS:
            return cached_df.copy()

    response = requests.get(
        AZS_URL,
        timeout=30,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
        },
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    city_blocks = soup.select(".t446__logo")
    prices_blocks = soup.select(".t431__data-part2")
    headers_blocks = soup.select(".t431__data-part1")

    if not city_blocks or not prices_blocks or not headers_blocks:
        raise ValueError("Не удалось найти таблицу цен АЗС на сайте oilclub.kz")

    headers = _split_semicolon(headers_blocks[0].get_text(" "))

    rows: list[dict[str, Any]] = []

    for city_block, price_block in zip(city_blocks, prices_blocks):
        title = _clean_text(city_block.get_text(" "))

        if " на " in title:
            city, date = title.split(" на ", 1)
        else:
            city, date = title, ""

        city = _clean_text(city)
        date = _clean_text(date)

        lines = [
            line.strip()
            for line in price_block.get_text("\n").splitlines()
            if line.strip()
        ]

        for line in lines:
            values = _split_semicolon(line)

            if len(values) < len(headers):
                values += [""] * (len(headers) - len(values))

            row: dict[str, Any] = {
                "Дата обновления": date,
                "Город": city,
            }

            for header, value in zip(headers, values):
                row[header] = value

            rows.append(row)

    df = pd.DataFrame(rows)

    if df.empty:
        raise ValueError("Сайт oilclub.kz загрузился, но данные АЗС не были распознаны")

    df.columns = [_clean_text(c) for c in df.columns]

    AZS_CACHE = (now, df.copy())

    return df


def get_azs_cities() -> list[str]:
    df = fetch_azs_prices()

    if "Город" not in df.columns:
        return []

    return sorted(
        {
            _clean_text(city)
            for city in df["Город"].dropna().tolist()
            if _clean_text(city)
        }
    )


def get_azs_fuels() -> list[str]:
    df = fetch_azs_prices()
    return [fuel for fuel in FUEL_COLUMNS if fuel in df.columns]


def generate_azs_report(city: str, fuel: str) -> Path:
    df = fetch_azs_prices()

    if "Город" not in df.columns or fuel not in df.columns:
        data_df = pd.DataFrame(
            [{"message": "Не найдены необходимые данные по выбранному городу или виду топлива"}]
        )

        return _write_report(
            title=f"АЗС_{city}_{fuel}",
            meta_rows=[
                {"Поле": "Ошибка", "Значение": "Не найдены необходимые данные"},
                {"Поле": "Источник", "Значение": AZS_URL},
            ],
            data_df=data_df,
            chart_df=pd.DataFrame(),
        )

    result = df[df["Город"].map(_clean_text).eq(city)].copy()

    result["Цена"] = result[fuel].map(_clean_price)
    result = result[result["Цена"].notna()].copy()
    result = result.sort_values("Цена")

    keep_cols = [
        c
        for c in ["Дата обновления", "Город", "АЗС", fuel, "Цена"]
        if c in result.columns
    ]

    result = result[keep_cols].copy()

    chart_df = pd.DataFrame()

    if not result.empty and "АЗС" in result.columns:
        chart_df = result[["АЗС", "Цена"]].copy()
        chart_df = chart_df.rename(columns={"Цена": fuel})

    date_values = (
        result["Дата обновления"].dropna().astype(str).unique().tolist()
        if "Дата обновления" in result.columns
        else []
    )

    meta = [
        {"Поле": "Источник", "Значение": AZS_URL},
        {"Поле": "Раздел", "Значение": "Мониторинг цен АЗС РК"},
        {"Поле": "Город", "Значение": city},
        {"Поле": "Вид топлива", "Значение": fuel},
        {"Поле": "Дата обновления", "Значение": ", ".join(date_values[:5])},
        {"Поле": "Строк в отчёте", "Значение": len(result)},
    ]

    return _write_report(
        title=f"АЗС_{city}_{fuel}",
        meta_rows=meta,
        data_df=result,
        chart_df=chart_df,
        chart_type="single",
    )