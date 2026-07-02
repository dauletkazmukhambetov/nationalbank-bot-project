from __future__ import annotations

import json
import re
import time
from pathlib import Path

import pandas as pd
import requests

from services.local_excel_service import _write_report, FX_CURRENCIES, FX_OPERATIONS


CITY_SLUGS = {
    "Астана": "astana",
    "Алматы": "almaty",
    "Шымкент": "shymkent",
    "Актобе": "aktobe",
    "Костанай": "kostanay",
    "Павлодар": "pavlodar",
    "Семей": "semei",
    "Талдыкорган": "taldykorgan",
    "Уральск": "uralsk",
}

FX_CACHE: dict[str, tuple[float, pd.DataFrame]] = {}
CACHE_TTL_SECONDS = 300


def _clean_phone(value: object) -> str:
    if isinstance(value, list):
        return ", ".join(str(x).strip() for x in value if str(x).strip())
    return "" if value is None else str(value).strip()


def _extract_punkts_json(html: str) -> list[dict]:
    marker = "var punkts = "
    start = html.find(marker)

    if start == -1:
        raise ValueError("Не удалось найти переменную 'var punkts' на странице kurs.kz.")

    start += len(marker)
    end = html.find(";\n", start)

    if end == -1:
        end = html.find(";</script>", start)

    if end == -1:
        raise ValueError("Не удалось определить конец JSON-массива 'punkts'.")

    raw_json = html[start:end].strip()

    try:
        return json.loads(raw_json)
    except json.JSONDecodeError as error:
        raise ValueError(f"Не удалось распарсить JSON 'punkts': {error}") from error


def get_fx_cities() -> list[str]:
    return list(CITY_SLUGS.keys())


def get_fx_currencies(city: str | None = None) -> list[str]:
    return FX_CURRENCIES.copy()


def fetch_fx_city(city: str) -> pd.DataFrame:
    if city not in CITY_SLUGS:
        raise ValueError(f"Город не поддерживается: {city}")

    now = time.time()

    if city in FX_CACHE:
        cached_time, cached_df = FX_CACHE[city]
        if now - cached_time < CACHE_TTL_SECONDS:
            return cached_df.copy()

    url = f"https://kurs.kz/site/index?city={CITY_SLUGS[city]}"

    response = requests.get(
        url,
        timeout=30,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
        },
    )
    response.raise_for_status()

    offices = _extract_punkts_json(response.text)

    rows: list[dict[str, object]] = []

    for office in offices:
        row: dict[str, object] = {
            "Обменный пункт": office.get("name", ""),
            "Адрес": office.get("mainaddress") or office.get("address", ""),
            "Телефон": _clean_phone(office.get("phones")),
            "ID": office.get("id", ""),
        }

        rates = office.get("data", {})

        for currency in FX_CURRENCIES:
            values = rates.get(currency)

            if isinstance(values, list) and len(values) == 2:
                buy, sell = values
                row[f"Покупка {currency}"] = None if buy == 0 else buy
                row[f"Продажа {currency}"] = None if sell == 0 else sell
            else:
                row[f"Покупка {currency}"] = None
                row[f"Продажа {currency}"] = None

        rows.append(row)

    df = pd.DataFrame(rows)

    if df.empty:
        raise ValueError(f"Данные kurs.kz загрузились, но обменники для города {city} не найдены.")

    FX_CACHE[city] = (now, df.copy())

    return df


def generate_fx_report(city: str, currency: str, operation: str) -> Path:
    df = fetch_fx_city(city)

    currency = currency.upper()
    operation = operation if operation in FX_OPERATIONS else "both"

    buy_col = f"Покупка {currency}"
    sell_col = f"Продажа {currency}"

    if buy_col not in df.columns and sell_col not in df.columns:
        data_df = pd.DataFrame([{"message": f"Нет данных по валюте {currency}"}])
        return _write_report(
            title=f"Обменники_{city}_{currency}_{operation}",
            meta_rows=[{"Поле": "Ошибка", "Значение": f"Нет данных по валюте {currency}"}],
            data_df=data_df,
            chart_df=pd.DataFrame(),
        )

    result = df.copy()

    value_cols: list[str] = []

    if operation in ("buy", "both") and buy_col in result.columns:
        value_cols.append(buy_col)

    if operation in ("sell", "both") and sell_col in result.columns:
        value_cols.append(sell_col)

    selected_cols = [
        c
        for c in ["Обменный пункт", "Адрес", "Телефон", "ID", buy_col, sell_col]
        if c in result.columns
    ]

    result = result[selected_cols].copy()

    if value_cols:
        result = result.dropna(subset=value_cols, how="all").copy()

    chart_df = pd.DataFrame()

    if "Обменный пункт" in result.columns and value_cols:
        chart_df = result[["Обменный пункт"] + value_cols].copy().head(30)

    meta = [
        {"Поле": "Источник", "Значение": f"https://kurs.kz/site/index?city={CITY_SLUGS[city]}"},
        {"Поле": "Раздел", "Значение": "Курсы валют в обменных пунктах"},
        {"Поле": "Город", "Значение": city},
        {"Поле": "Валюта", "Значение": currency},
        {"Поле": "Операция", "Значение": FX_OPERATIONS.get(operation, operation)},
        {"Поле": "Строк в отчёте", "Значение": len(result)},
    ]

    return _write_report(
        title=f"Обменники_{city}_{currency}_{operation}",
        meta_rows=meta,
        data_df=result,
        chart_df=chart_df,
        chart_type="double" if operation == "both" else "single",
    )