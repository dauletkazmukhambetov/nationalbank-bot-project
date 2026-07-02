from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd


def find_date_column(df: pd.DataFrame) -> str | None:
    candidates = (
        "Дата",
        "date",
        "reportDate",
        "reporting_date",
        "period",
        "Период",
        "Месяц",
        "Date",
    )

    for col in candidates:
        if col in df.columns:
            return col

    return None


def find_value_column(df: pd.DataFrame) -> str | None:
    """
    Определяет колонку с основным числовым показателем.
    Игнорирует технические числовые поля.
    """

    priority = (
        "Значение",
        "Цена",
        "amount",
        "value",
        "Курс",
        "Покупка",
        "Продажа",
    )

    skip_cols = {
        "Телефон",
        "phone",
        "ID",
        "id",
        "№",
        "No",
        "Column8",
        "Адрес",
        "Обменный пункт",
        "Название",
        "Наименование",
    }

    # 1. Сначала ищем наиболее вероятные названия колонок
    for col in priority:
        if col in df.columns:
            numeric = pd.to_numeric(df[col], errors="coerce")
            if numeric.notna().sum() > 0:
                return col

    # 2. Потом ищем любую числовую колонку,
    #    но пропускаем технические поля
    for col in df.columns:

        if str(col).strip() in skip_cols:
            continue

        numeric = pd.to_numeric(df[col], errors="coerce")

        if numeric.notna().sum() == 0:
            continue

        # колонка должна содержать минимум половину числовых значений
        if numeric.notna().sum() < len(df) * 0.5:
            continue

        return col

    return None


def prepare_series(df: pd.DataFrame) -> pd.DataFrame:
    date_col = find_date_column(df)
    value_col = find_value_column(df)

    if not value_col:
        return pd.DataFrame()

    result = df.copy()

    if date_col:
        result[date_col] = pd.to_datetime(result[date_col], errors="coerce")
        result[value_col] = pd.to_numeric(result[value_col], errors="coerce")

        result = result.dropna(subset=[date_col, value_col])
        result = (
            result
            .groupby(date_col, as_index=False)[value_col]
            .mean()
            .sort_values(date_col)
        )

        return result.rename(columns={
            date_col: "period",
            value_col: "value",
        })

    result[value_col] = pd.to_numeric(result[value_col], errors="coerce")
    result = result.dropna(subset=[value_col]).reset_index(drop=True)

    result["period"] = result.index + 1

    return result.rename(columns={
        value_col: "value",
    })[["period", "value"]]


def analyze_dataframe(df: pd.DataFrame, title: str = "Показатель") -> dict:
    series = prepare_series(df)

    if series.empty or len(series) < 2:
        return {
            "title": title,
            "status": "not_enough_data",
            "message": "Недостаточно данных для анализа",
        }

    first_value = float(series["value"].iloc[0])
    previous_value = float(series["value"].iloc[-2])
    last_value = float(series["value"].iloc[-1])

    absolute_change = last_value - previous_value
    percent_change = (
        absolute_change / previous_value * 100
        if previous_value != 0 else None
    )

    total_change = last_value - first_value
    total_percent_change = (
        total_change / first_value * 100
        if first_value != 0 else None
    )

    max_idx = series["value"].idxmax()
    min_idx = series["value"].idxmin()

    max_value = float(series.loc[max_idx, "value"])
    min_value = float(series.loc[min_idx, "value"])

    average_value = float(series["value"].mean())

    positive_steps = int((series["value"].diff() > 0).sum())
    negative_steps = int((series["value"].diff() < 0).sum())

    if total_change > 0 and positive_steps >= negative_steps:
        trend = "рост"
    elif total_change < 0 and negative_steps >= positive_steps:
        trend = "снижение"
    else:
        trend = "волатильная динамика"

    if percent_change is None:
        last_period_summary = "Изменение к предыдущему периоду невозможно рассчитать из-за нулевой базы."
    elif percent_change > 0:
        last_period_summary = f"Последнее значение выросло на {percent_change:.1f}% к предыдущему периоду."
    elif percent_change < 0:
        last_period_summary = f"Последнее значение снизилось на {abs(percent_change):.1f}% к предыдущему периоду."
    else:
        last_period_summary = "Последнее значение не изменилось к предыдущему периоду."

    if total_percent_change is None:
        total_summary = "Общее изменение за период невозможно рассчитать из-за нулевой базы."
    elif total_percent_change > 0:
        total_summary = f"За весь период показатель вырос на {total_percent_change:.1f}%."
    elif total_percent_change < 0:
        total_summary = f"За весь период показатель снизился на {abs(total_percent_change):.1f}%."
    else:
        total_summary = "За весь период показатель не изменился."

    return {
        "title": title,
        "status": "ok",
        "points_count": int(len(series)),
        "first_value": round(first_value, 2),
        "previous_value": round(previous_value, 2),
        "last_value": round(last_value, 2),
        "absolute_change": round(absolute_change, 2),
        "percent_change": round(percent_change, 2) if percent_change is not None else None,
        "total_change": round(total_change, 2),
        "total_percent_change": round(total_percent_change, 2) if total_percent_change is not None else None,
        "max_value": round(max_value, 2),
        "min_value": round(min_value, 2),
        "average_value": round(average_value, 2),
        "positive_steps": positive_steps,
        "negative_steps": negative_steps,
        "trend": trend,
        "summary": f"{last_period_summary} {total_summary} Общая динамика: {trend}.",
    }


def analyze_excel_report(path: str | Path) -> dict:
    path = Path(path)

    df = pd.read_excel(path, sheet_name="Данные")

    title = path.stem

    try:
        meta = pd.read_excel(path, sheet_name="Описание")
        if "Поле" in meta.columns and "Значение" in meta.columns:
            title_row = meta[meta["Поле"].astype(str).str.lower() == "показатель"]
            if not title_row.empty:
                title = str(title_row["Значение"].iloc[0])
    except Exception:
        pass

    return analyze_dataframe(df, title=title)


def main() -> None:
    if len(sys.argv) < 2:
        print("Укажи путь к Excel-отчёту")
        print(r"Пример: python analysis/economic_analyzer.py C:\path\report.xlsx")
        return

    result = analyze_excel_report(sys.argv[1])

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()