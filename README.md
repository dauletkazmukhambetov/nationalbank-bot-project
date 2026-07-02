# 📊 EcoMind
### AI-Powered Economic Analytics Platform

> A modular Telegram platform for collecting, analyzing, and visualizing economic data from the National Bank of Kazakhstan and external financial sources.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Aiogram](https://img.shields.io/badge/Aiogram-3.x-green)
![Pandas](https://img.shields.io/badge/Pandas-Data%20Analysis-purple)
![OpenPyXL](https://img.shields.io/badge/OpenPyXL-Excel-success)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)

---

# 📌 Overview

EcoMind is an AI-ready economic analytics platform developed during an industrial internship.

The system automatically retrieves economic indicators from the National Bank of Kazakhstan, exchange rates, and fuel prices from external financial sources. It processes the collected data, generates Excel reports with charts, performs statistical analysis, and prepares structured prompts for future AI-generated Telegram publications.

The platform is designed using a modular architecture that allows new data providers, analytics modules, and LLMs to be integrated with minimal changes.

---

# ✨ Features

- 📈 National Bank of Kazakhstan Open Data API integration
- 💱 Exchange rates monitoring (Kurs.kz)
- ⛽ Fuel price monitoring (OilClub.kz)
- 📊 Automatic Excel report generation
- 📉 Automatic chart generation
- 📋 Metadata generation
- 📁 XLSX export
- ⚡ Five-minute caching
- 🔍 Indicator filtering
- 📚 Knowledge base integration
- 🤖 AI prompt generation
- 🧠 Economic trend analysis
- 📨 Telegram Bot interface

---

# 🏗 System Architecture

> Overall platform architecture.


images/system_architecture.png

The platform follows a layered architecture:

- User Layer
- Telegram Application Layer
- External Data Sources
- Data Processing Layer
- AI / LLM Layer
- Output Layer

This design allows every component to evolve independently while keeping the system scalable and maintainable.

---

# 🔄 Data Flow

> End-to-end processing pipeline from user request to publication-ready content.

**⬇️ INSERT DIAGRAM 2 HERE**

```
images/data_flow.png
```

Processing pipeline:

1. User sends a request
2. Telegram bot routes the request
3. Data is retrieved from APIs and external sources
4. Filtering and preprocessing
5. Excel report generation
6. Economic analysis
7. Knowledge base search
8. Prompt construction
9. LLM processing
10. Publication-ready output

---

# 🏛 Project Architecture

```
EcoMind
│
├── Telegram Bot (Aiogram)
│
├── Services
│   ├── National Bank API
│   ├── Kurs.kz
│   ├── OilClub.kz
│   ├── Report Filters
│   ├── Economic Analyzer
│   ├── Prompt Builder
│   ├── Knowledge Search
│   ├── Excel Generator
│   └── Chart Generator
│
├── Knowledge Base
│
├── Reports
│
└── Configuration
```

---

# 📂 Repository Structure

```
services/
│
├── api_client.py
├── azs_web_service.py
├── fx_web_service.py
├── excel_generator.py
├── graph_generator.py
├── report_filters.py
├── economic_analyzer.py
├── prompt_builder.py
├── knowledge_search.py
│
analysis/
knowledge/
models/
reports/
data/

main.py
config.py
```

---

# ⚙ Technologies

## Backend

- Python 3.11
- Aiogram 3.x
- Requests
- BeautifulSoup
- Pandas
- OpenPyXL

## Data Processing

- JSON APIs
- HTML Parsing
- Data Cleaning
- Filtering
- Statistical Analysis

## Report Generation

- Excel
- Charts
- Metadata Sheets

## AI Preparation

- Prompt Engineering
- Knowledge Retrieval
- Similar Publications Search

---

# 📡 Data Sources

| Source | Purpose |
|---------|----------|
| National Bank of Kazakhstan API | Economic indicators |
| Kurs.kz | Exchange rates |
| OilClub.kz | Fuel prices |
| Internal Knowledge Base | AI prompt generation |

---

# 📊 Generated Reports

The platform automatically generates:

- Excel reports
- Charts
- Economic summaries
- Metadata sheets
- Filtered datasets

---

# 🧠 AI Pipeline

The project is designed for future integration with any Large Language Model.

Supported architecture:

- OpenAI GPT
- Google Gemini
- Claude
- Local Llama
- Corporate LLM

The generated prompt already contains:

- Economic analysis
- Trend calculations
- Similar historical publications
- Channel writing style
- Metadata

---

# 🚀 Current Status

✅ Telegram Bot

✅ National Bank API integration

✅ Kurs.kz integration

✅ OilClub.kz integration

✅ Excel report generation

✅ Chart generation

✅ Economic analysis

✅ Knowledge base search

✅ AI prompt generation

⬜ Automatic Telegram publication

⬜ Corporate LLM integration

---

# 💡 Future Improvements

- Scheduled report generation
- PostgreSQL storage
- Airflow automation
- Interactive dashboards
- REST API
- Docker deployment
- CI/CD pipeline
- Vector database for semantic search
- Automatic Telegram publishing

---

# 👨‍💻 Author

**Daulet Kazmukhambetov**

Software Engineering Student

Astana IT University

Industrial Practice Project
