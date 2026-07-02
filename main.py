from __future__ import annotations

import asyncio
import logging
import tempfile
from pathlib import Path

import pandas as pd
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from config import BOT_TOKEN
from keyboards import (
    azs_cities_menu,
    azs_fuels_menu,
    fx_cities_menu,
    fx_currencies_menu,
    fx_operations_menu,
    home_menu,
    indicators_menu,
    main_menu,
    years_menu,
)
from services.api_client import fetch_json
from services.excel_generator import generate_report
from services.indicators import by_section, get_indicator, get_sections, load_indicators
from services.azs_web_service import (
    generate_azs_report,
    get_azs_cities,
    get_azs_fuels,
)

from services.azs_web_service import (
    generate_azs_report,
    get_azs_cities,
    get_azs_fuels,
)

from services.fx_web_service import (
    generate_fx_report,
    get_fx_cities,
    get_fx_currencies,
)
from analysis.economic_analyzer import analyze_excel_report
from services.prompt_builder import build_prompt_context, context_to_prompt


logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
INDICATORS = load_indicators()

USER_REPORTS: dict[int, dict] = {}


def _sections() -> list[str]:
    return get_sections(INDICATORS)


def report_actions_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🤖 Анализ отчёта",
                    callback_data="report:analyze",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📝 Подготовить пост",
                    callback_data="report:post",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏠 Главное меню",
                    callback_data="home",
                )
            ],
        ]
    )


@dp.message(CommandStart())
async def start(message: Message) -> None:
    text = (
        "👋 Добро пожаловать в TENGENOMIKA BOT 2.0\n\n"
        "Бот формирует Excel-отчёты по API Национального Банка РК "
        "и локальным Excel-источникам компании.\n\n"
        "Выберите раздел ниже 👇"
    )
    await message.answer(text, reply_markup=main_menu(_sections()))


@dp.callback_query(F.data == "home")
async def home(callback: CallbackQuery) -> None:
    await callback.message.answer(
        "🏠 Главное меню\n\nВыберите раздел ниже 👇",
        reply_markup=main_menu(_sections()),
    )
    await callback.answer()


# -------------------------
# API Национального Банка
# -------------------------

@dp.callback_query(F.data.startswith("section:"))
async def choose_section(callback: CallbackQuery) -> None:
    section_index = int(callback.data.split(":", 1)[1])
    sections = _sections()
    section = sections[section_index]
    items = by_section(INDICATORS, section)

    await callback.message.edit_text(
        f"🏦 {section}\n\nВыберите показатель:",
        reply_markup=indicators_menu(items),
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("indicator:"))
async def choose_indicator(callback: CallbackQuery) -> None:
    indicator_id = callback.data.split(":", 1)[1]
    indicator = get_indicator(INDICATORS, indicator_id)

    if not indicator:
        await callback.answer("Показатель не найден", show_alert=True)
        return

    await callback.message.edit_text(
        f"💡 Вы выбрали показатель: {indicator['name']}\n\nВыберите год:",
        reply_markup=years_menu(indicator_id),
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("year:"))
async def build_report(callback: CallbackQuery) -> None:
    _, indicator_id, year_text = callback.data.split(":", 2)
    year = int(year_text)
    indicator = get_indicator(INDICATORS, indicator_id)

    if not indicator:
        await callback.answer("Показатель не найден", show_alert=True)
        return

    await callback.message.edit_text(
        f"⏳ Формирую отчёт...\nПоказатель: {indicator['name']}\nГод: {year}",
    )

    try:
        payload = await fetch_json(indicator["api_url"], year)
        report_path = generate_report(indicator, year, payload)

        USER_REPORTS[callback.from_user.id] = {
            "report_path": str(report_path),
            "indicator_name": indicator["name"],
            "year": year,
        }

        await callback.message.answer_document(
            FSInputFile(report_path),
            caption=f"✅ Отчёт готов за {year} год",
            reply_markup=report_actions_menu(),
        )

    except Exception as exc:
        logging.exception("Report generation failed")
        await callback.message.answer(
            "❌ Не удалось сформировать отчёт.\n"
            f"Ошибка: {exc}",
            reply_markup=home_menu(),
        )

    await callback.answer()


# -------------------------
# Локальный Excel: Мониторинг цен АЗС
# -------------------------

@dp.callback_query(F.data == "local:azs")
async def choose_azs_city(callback: CallbackQuery) -> None:
    cities = get_azs_cities()

    await callback.message.edit_text(
        "⛽ Мониторинг цен АЗС РК\n\nВыберите город:",
        reply_markup=azs_cities_menu(cities),
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("azs_city:"))
async def choose_azs_fuel(callback: CallbackQuery) -> None:
    city_index = int(callback.data.split(":", 1)[1])
    cities = get_azs_cities()

    if city_index >= len(cities):
        await callback.answer("Город не найден", show_alert=True)
        return

    fuels = get_azs_fuels()
    city = cities[city_index]

    await callback.message.edit_text(
        f"⛽ {city}\n\nВыберите вид топлива:",
        reply_markup=azs_fuels_menu(city_index, fuels),
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("azs_fuel:"))
async def build_azs_report(callback: CallbackQuery) -> None:
    _, city_index_text, fuel_index_text = callback.data.split(":", 2)
    city_index = int(city_index_text)
    fuel_index = int(fuel_index_text)

    cities = get_azs_cities()
    fuels = get_azs_fuels()

    if city_index >= len(cities) or fuel_index >= len(fuels):
        await callback.answer("Фильтр не найден", show_alert=True)
        return

    city = cities[city_index]
    fuel = fuels[fuel_index]

    await callback.message.edit_text(
        f"⏳ Формирую отчёт по АЗС...\nГород: {city}\nТопливо: {fuel}",
    )

    try:
        report_path = generate_azs_report(city, fuel)

        USER_REPORTS[callback.from_user.id] = {
            "report_path": str(report_path),
            "indicator_name": f"АЗС: {city}, {fuel}",
            "year": 0,
        }

        await callback.message.answer_document(
            FSInputFile(report_path),
            caption=f"✅ Отчёт готов: {city}, {fuel}",
            reply_markup=report_actions_menu(),
        )

    except Exception as exc:
        logging.exception("AZS report generation failed")
        await callback.message.answer(
            "❌ Не удалось сформировать отчёт по АЗС.\n"
            f"Ошибка: {exc}",
            reply_markup=home_menu(),
        )

    await callback.answer()


# -------------------------
# Локальный Excel: Курсы валют в обменных пунктах
# -------------------------

@dp.callback_query(F.data == "local:fx")
async def choose_fx_city(callback: CallbackQuery) -> None:
    cities = get_fx_cities()

    await callback.message.edit_text(
        "💱 Курсы валют в обменных пунктах\n\nВыберите город:",
        reply_markup=fx_cities_menu(cities),
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("fx_city:"))
async def choose_fx_currency(callback: CallbackQuery) -> None:
    city_index = int(callback.data.split(":", 1)[1])
    cities = get_fx_cities()

    if city_index >= len(cities):
        await callback.answer("Город не найден", show_alert=True)
        return

    city = cities[city_index]
    currencies = get_fx_currencies(city)

    await callback.message.edit_text(
        f"💱 {city}\n\nВыберите валюту:",
        reply_markup=fx_currencies_menu(city_index, currencies),
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("fx_curr:"))
async def choose_fx_operation(callback: CallbackQuery) -> None:
    _, city_index_text, currency = callback.data.split(":", 2)
    city_index = int(city_index_text)
    cities = get_fx_cities()

    if city_index >= len(cities):
        await callback.answer("Город не найден", show_alert=True)
        return

    city = cities[city_index]

    await callback.message.edit_text(
        f"💱 {city}\nВалюта: {currency}\n\nВыберите операцию:",
        reply_markup=fx_operations_menu(city_index, currency),
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("fx_op:"))
async def build_fx_report(callback: CallbackQuery) -> None:
    _, city_index_text, currency, operation = callback.data.split(":", 3)
    city_index = int(city_index_text)
    cities = get_fx_cities()

    if city_index >= len(cities):
        await callback.answer("Город не найден", show_alert=True)
        return

    city = cities[city_index]

    await callback.message.edit_text(
        f"⏳ Формирую отчёт по обменным пунктам...\nГород: {city}\nВалюта: {currency}",
    )

    try:
        report_path = generate_fx_report(city, currency, operation)

        USER_REPORTS[callback.from_user.id] = {
            "report_path": str(report_path),
            "indicator_name": f"Обменники: {city}, {currency}, {operation}",
            "year": 0,
        }

        await callback.message.answer_document(
            FSInputFile(report_path),
            caption=f"✅ Отчёт готов: {city}, {currency}",
            reply_markup=report_actions_menu(),
        )

    except Exception as exc:
        logging.exception("FX report generation failed")
        await callback.message.answer(
            "❌ Не удалось сформировать отчёт по обменным пунктам.\n"
            f"Ошибка: {exc}",
            reply_markup=home_menu(),
        )

    await callback.answer()


# -------------------------
# Анализ отчёта и подготовка ИИ-поста
# -------------------------

@dp.callback_query(F.data == "report:analyze")
async def analyze_last_report(callback: CallbackQuery) -> None:
    report = USER_REPORTS.get(callback.from_user.id)

    if not report:
        await callback.message.answer(
            "❌ Последний отчёт не найден. Сначала сформируйте отчёт.",
            reply_markup=home_menu(),
        )
        await callback.answer()
        return

    try:
        result = analyze_excel_report(report["report_path"])

        if result.get("status") != "ok":
            await callback.message.answer(
                "⚠️ Недостаточно данных для анализа отчёта.",
                reply_markup=home_menu(),
            )
            await callback.answer()
            return

        text = (
            "🤖 Анализ отчёта\n\n"
            f"📌 Показатель: {result.get('title')}\n"
            f"📊 Тренд: {result.get('trend')}\n"
            f"🔢 Первое значение: {result.get('first_value')}\n"
            f"🔢 Последнее значение: {result.get('last_value')}\n"
            f"↔️ Предыдущее значение: {result.get('previous_value')}\n"
            f"📈 Изменение к предыдущему периоду: {result.get('percent_change')}%\n"
            f"📊 Изменение за весь период: {result.get('total_percent_change')}%\n"
            f"⬆️ Максимум: {result.get('max_value')}\n"
            f"⬇️ Минимум: {result.get('min_value')}\n"
            f"📉 Среднее значение: {result.get('average_value')}\n\n"
            f"📝 Вывод:\n{result.get('summary')}"
        )

        await callback.message.answer(text, reply_markup=home_menu())

    except Exception as exc:
        logging.exception("Report analysis failed")
        await callback.message.answer(
            "❌ Не удалось проанализировать отчёт.\n"
            f"Ошибка: {exc}",
            reply_markup=home_menu(),
        )

    await callback.answer()


@dp.callback_query(F.data == "report:post")
async def prepare_post_prompt(callback: CallbackQuery) -> None:
    report = USER_REPORTS.get(callback.from_user.id)

    if not report:
        await callback.message.answer(
            "❌ Последний отчёт не найден. Сначала сформируйте отчёт.",
            reply_markup=home_menu(),
        )
        await callback.answer()
        return

    try:
        df = pd.read_excel(report["report_path"], sheet_name="Данные")

        context = build_prompt_context(
            indicator_name=report["indicator_name"],
            year=int(report.get("year") or 0),
            df=df,
            channel="tengenomika",
        )

        prompt = context_to_prompt(context)

        temp_dir = Path(tempfile.gettempdir())
        prompt_path = temp_dir / "ai_post_prompt.txt"
        prompt_path.write_text(prompt, encoding="utf-8")

        await callback.message.answer_document(
            FSInputFile(prompt_path),
            caption=(
                "📝 Промпт для ИИ-поста подготовлен.\n\n"
                "Пилотный режим: бот уже собирает аналитику отчёта, "
                "стиль канала и похожие публикации. "
                "Для автоматической генерации поста нужно подключить "
                "корпоративную LLM/API."
            ),
            reply_markup=home_menu(),
        )

    except Exception as exc:
        logging.exception("Prompt generation failed")
        await callback.message.answer(
            "❌ Не удалось подготовить промпт для поста.\n"
            f"Ошибка: {exc}",
            reply_markup=home_menu(),
        )

    await callback.answer()


async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())