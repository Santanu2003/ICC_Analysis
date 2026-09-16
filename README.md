# 🏏 ICC Tournaments Analytics

### *ODI World Cup, T20 World Cup, Champions Trophy & World Test Championship — one dashboard*

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-Data-150458?logo=pandas&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Ready-4169E1?logo=postgresql&logoColor=white)
![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)
![Vite](https://img.shields.io/badge/Vite-Bundler-646CFF?logo=vite&logoColor=white)
![Recharts](https://img.shields.io/badge/Recharts-Charts-22B5BF)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)

---

## 📖 About

Every completed ICC men's tournament across all four formats — **35 editions, 1,202
matches** — cleaned from 10 separate raw sources of wildly different shapes and quality,
cross-checked, and turned into one interactive analytics platform:

- **ODI World Cup** — 13 editions, 1975–2023 (501 matches)
- **T20 World Cup** — 10 editions, 2007–2026 (372 matches)
- **Champions Trophy** — 9 editions, 1998–2025 (128 matches)
- **World Test Championship** — all 3 completed cycles, 2019–2025 (201 matches)

An end-to-end pipeline (audit → clean per format → build a unified editions table →
validate) feeds a FastAPI REST API, with a PostgreSQL-ready schema for anyone who wants
to move it off CSVs, and a responsive React/Vite dashboard on top. This project pairs
with [FIFA World Cup Analytics](../fifa-app) and [Olympic Analysis](../olympic) as the
third entry in the same analytics-platform series.

## ✨ Features

| Page | What it shows |
|---|---|
| 🏠 **Dashboard** | Headline stats across all 4 formats + matches/editions-by-format charts |
| 🏆 **Editions** | Every edition's winner, runner-up, venue & POTM — searchable, filterable by tournament |
| 🏏 **Matches** | Every match ever played in any of the 4 formats, filterable by year/cycle and team |
| 🌍 **Teams** | All-time win/loss record per format, click through to a team's full match log |
| ⚔️ **Compare** | Head-to-head record between any two nations, within any one format |
| 📊 **Standings** | ODI World Cup group/points tables + World Test Championship final points tables |
| 🧑‍💼 **Players & Records** | T20 WC & Champions Trophy squad lists, all-time top-5 leaderboards, and a Statsguru-style detailed-stats browser (top 20 per category, or all of them where fewer than 20 exist) — consistent across all 4 formats, including WTC across all 3 cycles |

## 🗂️ Data quality notes (read before extending)

The 4 formats came from genuinely different sources with different completeness:

- **Champions Trophy** has no per-player stats file in the source data — only match
  results and squad lists. The API and UI reflect that; no records are fabricated for it.
- **WTC full player averages** (a Statsguru-style batting/bowling export) only ever
  existed for the 2019–21 cycle in the source data, with nothing equivalent for 2021–23
  or 2023–25. Rather than ship a feature that only worked for one of three cycles, it's
  been left out of the app entirely — WTC player-level records are covered by the
  `/api/wtc/records` top-5 leaderboards and the detailed-stats browser instead, both of
  which already span all 3 cycles.
- A large supplementary ball-by-ball ODI dataset (1,700 matches, 157K deliveries,
  28,911 players) exists in `data/raw/archive__12_/` but isn't wired into the pipeline —
  its match-tournament tagging is incomplete past 2019 and its CSV export is malformed.
  It's a good candidate for a future deep-dive (over-by-over analysis, player bios) but
  was out of scope here.

See `data/processed/validation_report.txt` (regenerate with
`python scripts/08_validate_data.py`) for the automated data-quality checks.

## 🛠️ Tech Stack

**Data** — Python, Pandas · **API** — FastAPI (PostgreSQL-ready schema) · **Frontend** —
React, Vite, Recharts · **Ops** — Docker

*(the live app runs straight off cleaned CSVs — no database required; Postgres is an
optional upgrade path, see [`database/schema.sql`](database/schema.sql) and
[`scripts/07_load_database.py`](scripts/07_load_database.py))*

## 📁 Project Structure

```
icc-app/
├── backend/                     # FastAPI app
│   └── app/main.py              #   → all REST endpoints
├── frontend/                    # React + Vite app
│   └── src/
│       ├── main.jsx             #   → every page/component
│       └── style.css
├── data/
│   ├── raw/                     # 10 untouched raw sources (see docs/DATA_SOURCES.md)
│   └── processed/               # cleaned, analytics-ready CSVs
├── scripts/                     # the pipeline, run in order 01 → 08
├── database/                    # optional Postgres schema + loader
├── docs/
├── run.py                       # one-command dev launcher
└── docker-compose.yml
```

## 🚀 Running it

**Quickest — one command** (needs Python 3 + Node.js installed):

```bash
python run.py
```

This creates a virtualenv, installs both backend and frontend dependencies, starts
both, and prints the dashboard URL (`http://localhost:5173`) once ready. Press
`Ctrl+C` to stop everything.

**Manually:**

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

**Docker (backend only):**

```bash
docker compose up --build
# API at http://localhost:8000
```

**Rebuilding the data pipeline** (only needed if you change the raw sources):

```bash
cd scripts
python 01_data_audit.py
python 02_clean_odi_wc.py
python 03_clean_t20_wc.py
python 04_clean_champions_trophy.py
python 05_clean_wtc.py
python 06_build_editions.py
python 08_validate_data.py
```

## 📡 API reference

Base URL: `/api`. Full interactive docs at `/docs` once the backend is running (FastAPI
auto-generates OpenAPI/Swagger UI).

| Endpoint | Description |
|---|---|
| `GET /formats` | The 4 tournament format keys/labels |
| `GET /editions` | All 35 editions across all formats (`?tournament=` filter) |
| `GET /editions/{tournament}/{year}` | One edition's detail |
| `GET /{fmt}/matches` | Matches for a format (`?year=` or `?cycle=` for WTC, `?team=`) |
| `GET /{fmt}/matches/{match_id}` | One match |
| `GET /{fmt}/teams` | All-time win/loss stats per team, per format |
| `GET /{fmt}/teams/{team}` | One team's stats + full match log |
| `GET /{fmt}/teams/compare/{a}/{b}` | Head-to-head record between two teams |
| `GET /{fmt}/players` | Squad lists (`t20_wc` and `champions_trophy` only) |
| `GET /{fmt}/records` | Top-5 curated leaderboards (`?category=`, plus `?cycle=` for WTC) |
| `GET /{fmt}/detailed-stats` | Statsguru-style browser, top 20 per category (or all, if fewer exist) |
| `GET /{fmt}/detailed-stats/categories` | The list of detailed-stats categories available for a format |
| `GET /odi_wc/standings` | Group/points tables (`?year=`) |
| `GET /wtc/points-tables` | Final league table per cycle (`?cycle=`) |
| `GET /wtc/venues` | Venues used per cycle |
| `GET /statistics/overview` | Cross-format headline numbers |

`fmt` is one of `odi_wc`, `t20_wc`, `champions_trophy`, `wtc`.

## 📄 License

Built for educational/portfolio purposes. Underlying cricket data belongs to its
original sources; this project only reshapes it for analysis.
