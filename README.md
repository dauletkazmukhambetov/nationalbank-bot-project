# TENGENOMIKA BOT 2.0 — API + Excel источники

Telegram-бот формирует Excel-отчёты по API Национального Банка РК и локальным Excel-файлам компании. В отчётах создаются листы с описанием, данными и редактируемым графиком Excel.

## Что добавлено

### API Национального Банка РК

- меню строится из `data/indicators.json`;
- пользователь выбирает раздел → показатель → год;
- бот получает JSON через API;
- данные фильтруются по выбранному показателю и году;
- формируется `.xlsx` отчёт.

### Локальные Excel-источники

Добавлены два Excel-файла:

```text
data/excel_sources/Мониторинг цен АЗС РК_new.xlsx
data/excel_sources/Курсы валют в обменных пунктах.xlsx
```

В главном меню появились дополнительные разделы:

```text
⛽ Мониторинг цен АЗС РК
💱 Курсы валют в обменных пунктах
```

#### Мониторинг цен АЗС

Логика выбора:

```text
Город → Вид топлива → Excel-отчёт
```

Поддерживаемые виды топлива берутся из файла автоматически:

```text
АИ-92, АИ-92 Prime, АИ-95, АИ-95 Prime, АИ-98, ДТ, ДТЗ, ДТЗ (ПТФ-32), Газ
```

#### Курсы валют в обменных пунктах

Логика выбора:

```text
Город → Валюта → Покупка / Продажа / Покупка и продажа → Excel-отчёт
```

Поддерживаемые валюты:

```text
USD, EUR, RUB
```

## Установка

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Создайте файл `.env` рядом с `main.py`:

```env
BOT_TOKEN=ваш_токен_от_BotFather
```

## Запуск

```bash
python main.py
```

## Структура проекта

```text
nationalbank_bot_project_pro_filtered/
├── main.py
├── config.py
├── keyboards.py
├── requirements.txt
├── .env.example
├── data/
│   ├── indicators.json
│   └── excel_sources/
│       ├── Мониторинг цен АЗС РК_new.xlsx
│       └── Курсы валют в обменных пунктах.xlsx
└── services/
    ├── api_client.py
    ├── excel_generator.py
    ├── graph_generator.py
    ├── indicators.py
    ├── local_excel_service.py
    └── report_filters.py
```

## Основные файлы

- `main.py` — обработчики Telegram-кнопок и маршрутизация между API и Excel-источниками.
- `keyboards.py` — inline-кнопки для API, АЗС и обменных пунктов.
- `services/api_client.py` — получение данных из API.
- `services/excel_generator.py` — формирование отчётов по API.
- `services/local_excel_service.py` — чтение локальных Excel-файлов, фильтрация и генерация отчётов.
- `services/report_filters.py` — фильтры по `form_id` для API Национального Банка.

