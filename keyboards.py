from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

YEARS = [2020, 2021, 2022, 2023, 2024, 2025, 2026]


def main_menu(sections: list[str]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for index, section in enumerate(sections):
        builder.button(text=section[:60], callback_data=f"section:{index}")

    builder.button(text="⛽ Мониторинг цен АЗС РК", callback_data="local:azs")
    builder.button(text="💱 Курсы валют в обменных пунктах", callback_data="local:fx")
    builder.adjust(1)
    return builder.as_markup()


def indicators_menu(items: list[dict]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for item in items:
        button_text = item.get("menu_name") or item["name"]

        builder.button(
            text=button_text[:60],
            callback_data=f"indicator:{item['id']}"
        )

    builder.button(text="🏠 Главное меню", callback_data="home")
    builder.adjust(1)
    return builder.as_markup()


def years_menu(indicator_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for year in YEARS:
        builder.button(text=str(year), callback_data=f"year:{indicator_id}:{year}")
    builder.button(text="❌ Отмена", callback_data="home")
    builder.adjust(2)
    return builder.as_markup()


def azs_cities_menu(cities: list[str]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for index, city in enumerate(cities):
        builder.button(text=city[:60], callback_data=f"azs_city:{index}")
    builder.button(text="🏠 Главное меню", callback_data="home")
    builder.adjust(1)
    return builder.as_markup()


def azs_fuels_menu(city_index: int, fuels: list[str]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for index, fuel in enumerate(fuels):
        builder.button(text=fuel[:60], callback_data=f"azs_fuel:{city_index}:{index}")
    builder.button(text="⬅️ Назад", callback_data="local:azs")
    builder.button(text="🏠 Главное меню", callback_data="home")
    builder.adjust(2)
    return builder.as_markup()


def fx_cities_menu(cities: list[str]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for index, city in enumerate(cities):
        builder.button(text=city[:60], callback_data=f"fx_city:{index}")
    builder.button(text="🏠 Главное меню", callback_data="home")
    builder.adjust(1)
    return builder.as_markup()


def fx_currencies_menu(city_index: int, currencies: list[str]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for currency in currencies:
        builder.button(text=currency, callback_data=f"fx_curr:{city_index}:{currency}")
    builder.button(text="⬅️ Назад", callback_data="local:fx")
    builder.button(text="🏠 Главное меню", callback_data="home")
    builder.adjust(3)
    return builder.as_markup()


def fx_operations_menu(city_index: int, currency: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Покупка", callback_data=f"fx_op:{city_index}:{currency}:buy")
    builder.button(text="Продажа", callback_data=f"fx_op:{city_index}:{currency}:sell")
    builder.button(text="Покупка и продажа", callback_data=f"fx_op:{city_index}:{currency}:both")
    builder.button(text="⬅️ Назад", callback_data=f"fx_city:{city_index}")
    builder.button(text="🏠 Главное меню", callback_data="home")
    builder.adjust(1)
    return builder.as_markup()


def home_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🏠 Главное меню", callback_data="home")]])
