from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent.parent))

from services.prompt_builder import build_prompt_context, context_to_prompt


REPORT_PATH = r"C:\Users\Vivobook\Downloads\Telegram Desktop\Кредиты_экономике_в_расширенном_определении_всего_2025.xlsx"

df = pd.read_excel(REPORT_PATH, sheet_name="Данные")

context = build_prompt_context(
    indicator_name="Кредиты экономике в расширенном определении, всего",
    year=2025,
    df=df,
    channel="tengenomika",
)

prompt = context_to_prompt(context)

print(prompt)