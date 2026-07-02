from pathlib import Path
import tempfile

import matplotlib.pyplot as plt
import pandas as pd


def generate_graph(
    df: pd.DataFrame,
    indicator_name: str,
) -> Path | None:

    if df is None or df.empty:
        return None

    date_col = None

    for col in (
        "reportDate",
        "reporting_date",
        "date",
        "period",
        "Дата",
    ):
        if col in df.columns:
            date_col = col
            break

    if not date_col:
        return None

    value_col = None

    for col in df.columns:
        if col == date_col:
            continue

        numeric = pd.to_numeric(df[col], errors="coerce")

        if numeric.notna().sum() > 0:
            value_col = col
            break

    if not value_col:
        return None

    graph_df = df[[date_col, value_col]].copy()

    graph_df[date_col] = pd.to_datetime(
        graph_df[date_col],
        errors="coerce",
    )

    graph_df[value_col] = pd.to_numeric(
        graph_df[value_col],
        errors="coerce",
    )

    graph_df = graph_df.dropna()

    if graph_df.empty:
        return None

    graph_df = graph_df.sort_values(date_col)

    plt.figure(figsize=(12, 6))

    plt.plot(
        graph_df[date_col],
        graph_df[value_col],
        linewidth=2,
    )

    plt.title(indicator_name)
    plt.xlabel("Дата")
    plt.ylabel("Значение")
    plt.grid(True)

    plt.tight_layout()

    path = (
        Path(tempfile.gettempdir())
        / f"{indicator_name[:50]}_graph.png"
    )

    plt.savefig(path)
    plt.close()

    return path