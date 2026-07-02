from __future__ import annotations

import math
import re
import tempfile
from pathlib import Path
from typing import Literal

import pandas as pd
from openpyxl.chart import BarChart, Reference

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "excel_sources"
AZS_FILE = DATA_DIR / "Мониторинг цен АЗС РК_new.xlsx"
FX_FILE = DATA_DIR / "Курсы валют в обменных пунктах.xlsx"

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

FX_CURRENCIES = ["USD", "EUR", "RUB"]
FX_OPERATIONS = {
    "buy": "Покупка",
    "sell": "Продажа",
    "both": "Покупка и продажа",
}


def safe_filename(text: str) -> str:
    text = re.sub(r"[^0-9A-Za-zА-Яа-я_. -]+", "_", str(text))
    text = re.sub(r"\s+", "_", text).strip("_ .")
    return text[:120] or "report"


def _clean_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def _clean_price(value: object) -> float | None:
    text = _clean_text(value)
    if not text or text in {"-", "—", "nan", "None"}:
        return None
    # Examples: 238тг/л, 470.5, 6,12
    text = text.replace(",", ".")
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return None
    try:
        return float(match.group(0))
    except ValueError:
        return None


def _write_report(
    *,
    title: str,
    meta_rows: list[dict[str, object]],
    data_df: pd.DataFrame,
    chart_df: pd.DataFrame,
    chart_type: Literal["single", "double"] = "single",
) -> Path:
    temp_dir = Path(tempfile.gettempdir())
    path = temp_dir / f"{safe_filename(title)}.xlsx"

    if data_df is None or data_df.empty:
        data_df = pd.DataFrame([{"message": "По выбранному фильтру данных не найдено"}])

    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        pd.DataFrame(meta_rows).to_excel(writer, sheet_name="Описание", index=False)
        data_df.to_excel(writer, sheet_name="Данные", index=False)

        if chart_df is not None and not chart_df.empty and len(chart_df) >= 1:
            chart_df.to_excel(writer, sheet_name="График_данные", index=False)
            pd.DataFrame({"График": [""]}).to_excel(writer, sheet_name="График", index=False)
            ws_data = writer.sheets["График_данные"]
            ws_chart = writer.sheets["График"]

            chart = BarChart()
            chart.title = title
            chart.y_axis.title = "Значение"
            chart.x_axis.title = "Категория"
            chart.height = 14
            chart.width = 28

            max_row = len(chart_df) + 1
            max_col = 3 if chart_type == "double" and chart_df.shape[1] >= 3 else 2
            data = Reference(ws_data, min_col=2, max_col=max_col, min_row=1, max_row=max_row)
            cats = Reference(ws_data, min_col=1, min_row=2, max_row=max_row)
            chart.add_data(data, titles_from_data=True)
            chart.set_categories(cats)
            ws_chart.add_chart(chart, "A1")
        else:
            pd.DataFrame({"График": ["Недостаточно числовых данных для построения графика"]}).to_excel(
                writer,
                sheet_name="График",
                index=False,
            )

        for sheet_name in writer.sheets:
            ws = writer.sheets[sheet_name]
            for col in ws.columns:
                letter = col[0].column_letter
                max_len = 0
                for cell in col:
                    value = "" if cell.value is None else str(cell.value)
                    max_len = max(max_len, min(len(value), 60))
                ws.column_dimensions[letter].width = max(12, max_len + 2)
            ws.freeze_panes = "A2"

    return path


# -------------------------
# АЗС
# -------------------------

def read_azs() -> pd.DataFrame:
    df = pd.read_excel(AZS_FILE, sheet_name="Все АЗС")
    df.columns = [_clean_text(c) for c in df.columns]
    return df


def get_azs_cities() -> list[str]:
    df = read_azs()
    if "Город" not in df.columns:
        return []
    cities = sorted({_clean_text(x) for x in df["Город"].dropna().tolist() if _clean_text(x)})
    return cities


def get_azs_fuels() -> list[str]:
    df = read_azs()
    return [fuel for fuel in FUEL_COLUMNS if fuel in df.columns]


def generate_azs_report(city: str, fuel: str) -> Path:
    df = read_azs()
    if "Город" not in df.columns or fuel not in df.columns:
        data_df = pd.DataFrame([{"message": "Не найдены необходимые колонки в Excel-файле АЗС"}])
        return _write_report(
            title=f"АЗС_{city}_{fuel}",
            meta_rows=[{"Поле": "Ошибка", "Значение": "Не найдены необходимые колонки"}],
            data_df=data_df,
            chart_df=pd.DataFrame(),
        )

    result = df[df["Город"].map(_clean_text).eq(city)].copy()
    result["Цена"] = result[fuel].map(_clean_price)

    keep_cols = [c for c in ["Дата обновления", "Город", "АЗС", fuel, "Цена"] if c in result.columns]
    result = result[keep_cols].copy()
    result = result[result["Цена"].notna()].copy()
    result = result.sort_values("Цена")

    chart_df = pd.DataFrame()
    if not result.empty and "АЗС" in result.columns:
        chart_df = result[["АЗС", "Цена"]].rename(columns={"АЗС": "АЗС", "Цена": fuel})

    date_values = result["Дата обновления"].dropna().astype(str).unique().tolist() if "Дата обновления" in result.columns else []
    meta = [
        {"Поле": "Источник", "Значение": "Мониторинг цен АЗС РК_new.xlsx"},
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


# -------------------------
# Обменные пункты
# -------------------------

def get_fx_cities() -> list[str]:
    return pd.ExcelFile(FX_FILE).sheet_names


def get_fx_currencies(city: str | None = None) -> list[str]:
    # В файле используются USD/RUB/EUR. Оставляем все три валюты в меню.
    return FX_CURRENCIES.copy()


def read_fx_city(city: str) -> pd.DataFrame:
    df = pd.read_excel(FX_FILE, sheet_name=city)
    df.columns = [_clean_text(c) for c in df.columns]
    return df


def generate_fx_report(city: str, currency: str, operation: str) -> Path:
    df = read_fx_city(city)
    currency = currency.upper()
    operation = operation if operation in FX_OPERATIONS else "both"

    buy_col = f"Покупка {currency}"
    sell_col = f"Продажа {currency}"

    if buy_col not in df.columns and sell_col not in df.columns:
        data_df = pd.DataFrame([{"message": f"В листе {city} нет колонок по валюте {currency}"}])
        return _write_report(
            title=f"Обменники_{city}_{currency}_{operation}",
            meta_rows=[{"Поле": "Ошибка", "Значение": f"Нет данных по валюте {currency}"}],
            data_df=data_df,
            chart_df=pd.DataFrame(),
        )

    # Убираем итоговые строки, оставляем только обменные пункты.
    result = df.copy()
    name_col = "Обменный пункт"
    if name_col in result.columns:
        result = result[~result[name_col].astype(str).str.contains("Средний курс|Выгодная покупка", case=False, na=False)].copy()

    if buy_col in result.columns:
        result[buy_col] = result[buy_col].map(_clean_price)
    if sell_col in result.columns:
        result[sell_col] = result[sell_col].map(_clean_price)

    selected_cols = [c for c in [name_col, "Адрес", "Телефон", "Column8", buy_col, sell_col] if c in result.columns]
    result = result[selected_cols].copy()

    value_cols: list[str] = []
    if operation in ("buy", "both") and buy_col in result.columns:
        value_cols.append(buy_col)
    if operation in ("sell", "both") and sell_col in result.columns:
        value_cols.append(sell_col)

    if value_cols:
        result = result.dropna(subset=value_cols, how="all").copy()

    chart_df = pd.DataFrame()
    if name_col in result.columns and value_cols:
        chart_cols = [name_col] + value_cols
        chart_df = result[chart_cols].copy().head(30)
        chart_df = chart_df.rename(columns={name_col: "Обменный пункт"})

    meta = [
        {"Поле": "Источник", "Значение": "Курсы валют в обменных пунктах.xlsx"},
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
