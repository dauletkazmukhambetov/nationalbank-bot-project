from __future__ import annotations

import re
from typing import Any

import pandas as pd


def _norm(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value).lower().replace("ё", "е")).strip()


def _eq(series: pd.Series, value: str) -> pd.Series:
    return series.fillna("").map(_norm).eq(_norm(value))


def _contains(series: pd.Series, value: str) -> pd.Series:
    return series.fillna("").map(_norm).str.contains(re.escape(_norm(value)), na=False)


def _col(df: pd.DataFrame, *names: str) -> str | None:
    existing = {c.lower(): c for c in df.columns}
    for name in names:
        if name.lower() in existing:
            return existing[name.lower()]
    return None


def _and(mask: pd.Series | None, part: pd.Series) -> pd.Series:
    return part if mask is None else (mask & part)


def _generic_text_filter(df: pd.DataFrame, text: str) -> pd.DataFrame:
    if df.empty or not text:
        return df

    text = _norm(text)
    bad_words = {"в", "и", "по", "от", "из", "на", "за", "для", "с", "со", "г", "рк"}
    tokens = [
        t for t in re.split(r"[^0-9a-zа-я]+", text)
        if len(t) >= 4 and t not in bad_words
    ]

    if not tokens:
        return df

    str_cols = [c for c in df.columns if df[c].dtype == object]
    if not str_cols:
        return df

    joined = df[str_cols].fillna("").astype(str).agg(" ".join, axis=1).map(_norm)

    min_hits = 1 if len(tokens) <= 2 else 2
    hits = sum(joined.str.contains(re.escape(token), na=False) for token in tokens)

    result = df[hits >= min_hits]
    return result if not result.empty else df


def _joined_text(df: pd.DataFrame) -> pd.Series:
    text_cols = [c for c in df.columns if df[c].dtype == object]
    if not text_cols:
        return pd.Series([""] * len(df), index=df.index)

    return df[text_cols].fillna("").astype(str).agg(" ".join, axis=1).map(_norm)


def _filter_by_terms(df: pd.DataFrame, terms: list[str]) -> pd.DataFrame:
    if not terms:
        return df

    joined = _joined_text(df)
    mask = pd.Series(True, index=df.index)

    for term in terms:
        term_norm = _norm(term)

        if term_norm in ("business", "individuals"):
            pattern = rf"'attrcode': 'subject_type'.*?'valuecode': '{term_norm}'"
            mask = mask & joined.str.contains(pattern, case=False, regex=True, na=False)

        elif term_norm in ("kzt", "fx"):
            pattern = rf"'attrcode': 'currency'.*?'valuecode': '{term_norm}'"
            mask = mask & joined.str.contains(pattern, case=False, regex=True, na=False)

        else:
            mask = mask & joined.str.contains(re.escape(term_norm), regex=True, na=False)

    result = df[mask].copy()
    return result if not result.empty else df


def filter_dataframe(df: pd.DataFrame, indicator: dict[str, Any]) -> pd.DataFrame:
    if df.empty:
        return df

    form_id = str(indicator.get("form_id", ""))
    indicator_id = str(indicator.get("id", ""))
    name = str(indicator.get("name", ""))

    # PAGE_API: депозиты в депозитных организациях.
    if form_id == "PAGE_API":
        date_col = _col(df, "reporting_date", "date", "period", "reportDate")

        rules = {
            "78": "transferable_deposit_nc",
            "79": "other_deposit_nc",
            # id=80 "за декабрь 2019 данные с учетом заключительных оборотов" —
            # это не отдельный ряд данных, а сноска/примечание к показателю id=79
            # ("Другие депозиты в национальной валюте"). В исходной таблице НБРК
            # у него нет собственного столбца значений, поэтому явно алиасим
            # на тот же value_col, что и id=79, вместо падения в generic-фоллбэк.
            "80": "other_deposit_nc",
            "81": "transferable_deposit_nc_nb_le",
            "82": "other_deposit_nc_nb_le",
            "83": "transferable_deposit_fc_nb_le",
            "84": "other_deposit_fc_nb_le",
            "85": "transferable_deposit_nc_np",
            "86": "other_deposit_nc_np",
            "87": "transferable_deposit_fc_np",
            "88": "other_deposit_fc_np",
        }

        value_col = rules.get(indicator_id)

        if value_col and value_col in df.columns:
            keep_cols = []
            if date_col:
                keep_cols.append(date_col)

            keep_cols.append(value_col)

            result = df[keep_cols].copy()
            result = result.rename(columns={
                value_col: indicator.get("name", "value")
            })

            return result

    # form_id=470: Национальный фонд и финансовые инструменты.
    if form_id == "470":
        # Примечание: id=50 ("Трансферты из НФ") и id=51 ("Трансферт из
        # Национального фонда млрд тенге") намеренно маппятся на один и тот же
        # код 'TransNF' — id=50, судя по структуре исходной таблицы, является
        # краткой подписью/заголовком к полноценному показателю id=51 (та же
        # логика, что у пар "РЭОК"/"НЭОК" в form_id=299 ниже). Если в
        # будущем выяснится, что это разные ряды (например, разные единицы
        # измерения), нужно завести для id=50 отдельный код.
        rules = {
            "50": "TransNF",
            "51": "TransNF",
            "52": "OTH",
            "53": "USD",
            "54": "NFtg",
        }

        code = rules.get(indicator_id)

        if code:
            joined = _joined_text(df)

            mask = joined.str.contains(
                f"'valuecode': '{code.lower()}'",
                case=False,
                regex=False,
                na=False,
            )

            result = df[mask].copy()
            return result if not result.empty else df

    # form_id=33: официальный курс USDKZT.
    if form_id == "33":
        joined = _joined_text(df)

        mask = (
            joined.str.contains("'valuecode': 'usd'", case=False, regex=False, na=False)
            &
            joined.str.contains("'valuecode': 'monthly'", case=False, regex=False, na=False)
        )

        result = df[mask].copy()
        return result if not result.empty else df

    # form_id=299: индексы эффективных обменных курсов.
    if form_id == "299":
        category_col = _col(df, "attribute.category")
        subcategory_col = _col(df, "attribute.subcategory")
        pair_col = _col(df, "attribute.fx_currency_pair")

        # Примечание: id=28 ("НЭОК") и id=29 ("Номинальный эффективный
        # обменный курс") намеренно маппятся на одинаковый критерий
        # (nominal effective exchange rate / including). По аналогии с
        # заголовками "РЭОК" (id=24) в исходной таблице id=28, вероятно,
        # является краткой подписью-заголовком к полноценному показателю
        # id=29, а не отдельным рядом данных. Стоит перепроверить у
        # владельца данных, нужен ли для id=28 отдельный столбец.
        rules = {
            "27": {"category": "real effective exchange rate", "subcategory": "excluding"},
            "28": {"category": "nominal effective exchange rate", "subcategory": "including"},
            "29": {"category": "nominal effective exchange rate", "subcategory": "including"},
            "30": {"category": "nominal effective exchange rate", "subcategory": "excluding"},
            "32": {"category": "real exchange rate", "pair": "RUB"},
            "33": {"category": "real exchange rate", "pair": "EUR"},
            "34": {"category": "real exchange rate", "pair": "USD"},
            "35": {"category": "real exchange rate", "pair": "CNY"},
        }

        rule = rules.get(indicator_id)

        if rule:
            mask = None

            if category_col and "category" in rule:
                mask = _and(mask, _eq(df[category_col], rule["category"]))

            if subcategory_col and "subcategory" in rule:
                mask = _and(mask, _eq(df[subcategory_col], rule["subcategory"]))

            if pair_col and "pair" in rule:
                mask = _and(mask, _eq(df[pair_col], rule["pair"]))

            if mask is not None:
                result = df[mask].copy()
                return result if not result.empty else df

    # form_id=445: кредиты экономике в расширенном определении.
    if form_id == "445":
        rules = {
            "119": [],
            "120": ["banking sector"],
            "121": ["other organizations"],
            "122": ["mortgage sector"],
            "123": ["other public sector"],
            "124": ["microfinance sector"],
            "125": ["business"],
            "126": ["business", "kzt"],
            "127": ["business", "fx"],
            "128": ["individuals"],
            "129": ["individuals", "kzt"],
            "130": ["individuals", "fx"],
        }

        terms = rules.get(indicator_id)

        if terms is not None:
            return _filter_by_terms(df, terms)

    # form_id=28: покупка/продажа иностранной валюты по регионам.
    if form_id == "28":
        possible_cols = [
            c for c in df.columns
            if any(k in c.lower() for k in ("region", "oblast", "branch", "filial", "department", "area"))
        ]

        search_text = name.replace("г. ", "").replace("областной", "").strip()

        for c in possible_cols:
            result = df[_contains(df[c], search_text)].copy()
            if not result.empty:
                return result

        return _generic_text_filter(df, search_text)

    # form_id=479: платежный баланс.
    if form_id == "479":
        mapping = {
            "62": "BCA_BP6_USD",
            "63": "BG_BP6_USD",
            "64": "BS_BP6_USD",
            "65": "BIP_BP6_USD",
            "66": "BIS_BP6_USD",
        }

        code = mapping.get(indicator_id)

        if code:
            joined = _joined_text(df)

            mask = joined.str.contains(
                f"'valuecode': '{code.lower()}'",
                case=False,
                regex=False,
                na=False,
            )

            result = df[mask].copy()
            return result if not result.empty else df

    # form_id=476: реализация золота населению.
    if form_id == "476":
        return df

    # Готовые аналитические таблицы.
    if form_id in ("286", "287", "288", "289", "430"):
     return df

    # Остальные form_id: fallback по названию показателя.
    return _generic_text_filter(df, name)