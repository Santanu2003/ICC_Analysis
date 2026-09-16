<div align="center">

# 🏏 ICC Tournaments Analytics

### *ODI World Cup · T20 World Cup · Champions Trophy · World Test Championship*
### One dashboard for every ICC men's tournament ever played.

<br/>

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![Vite](https://img.shields.io/badge/Vite-Bundler-646CFF?style=for-the-badge&logo=vite&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-Data-150458?style=for-the-badge&logo=pandas&logoColor=white)

<br/>

### 🔗 [**View Live App →**](https://icc-analysis.vercel.app/)
`icc-analysis.vercel.app`

</div>

<br/>

---

## 📖 About

Every completed ICC men's tournament across all four formats — **35 editions,
1,202 matches** — cleaned from 10 raw sources of wildly different shapes and
quality, cross-checked, and turned into one interactive analytics platform.

<div align="center">

| 🏆 Tournament | Editions | Matches | Span |
|:---:|:---:|:---:|:---:|
| **ODI World Cup** | 13 | 501 | 1975 – 2023 |
| **T20 World Cup** | 10 | 372 | 2007 – 2026 |
| **Champions Trophy** | 9 | 128 | 1998 – 2025 |
| **World Test Championship** | 3 cycles | 201 | 2019 – 2025 |

</div>

An end-to-end data pipeline (**audit → clean per format → build a unified
editions table → validate**) feeds a FastAPI REST API, with a responsive
React + Vite dashboard on top.

<br/>

## ✨ Features

<div align="center">

| Page | What it shows |
|:---|:---|
| 🏠 **Dashboard** | Headline stats across all 4 formats + matches/editions-by-format charts |
| 🏆 **Editions** | Every edition's winner, runner-up, venue & POTM — searchable, filterable |
| 🏏 **Matches** | Every match ever played, filterable by year/cycle and team |
| 🌍 **Teams** | All-time win/loss record per format, with full match logs |
| ⚔️ **Compare** | Head-to-head record between any two nations, per format |
| 📊 **Standings** | ODI World Cup group/points tables + WTC final points tables |
| 🧑‍💼 **Players & Records** | Squad lists, top-5 leaderboards, and a detailed-stats browser |

</div>

<br/>

## 🏗️ Architecture

```
   ┌─────────────────────┐                          ┌──────────────────────┐
   │   React + Vite SPA   │  ── HTTPS / JSON ──────▶ │   FastAPI backend     │
   │   hosted on Vercel   │  ◀──────────────────────  │   hosted on Render    │
   └─────────────────────┘   VITE_API_URL = /api    └──────────────────────┘
                                                                 │
                                                                 ▼
                                                    Cleaned, analytics-ready
                                                    CSVs  (data/processed/)
```

> Frontend and backend are deployed **independently** and talk to each other
> purely over HTTP — no shared server, no shared build step.

- 🎨 **Frontend** — static Vite build on **Vercel**, reading the API base URL
  from `VITE_API_URL` at build time.
- ⚙️ **Backend** — FastAPI web service on **Render**, serving data straight
  from pre-cleaned CSVs (no database needed — Postgres is an optional
  upgrade path via `database/schema.sql`).
- 🔓 CORS on the backend is fully open, so the two can live on completely
  different domains with zero extra config.

<br/>

## 📁 Project Structure

```
icc-app/
├── backend/                     # FastAPI app
│   ├── app/main.py              #   → all REST endpoints
│   └── requirements.txt
├── frontend/                    # React + Vite app
│   └── src/
│       ├── main.jsx             #   → every page/component
│       └── style.css
├── data/
│   ├── raw/                     # untouched raw sources
│   └── processed/               # cleaned, analytics-ready CSVs
├── scripts/                     # data pipeline, run in order 01 → 08
├── database/                    # optional Postgres schema + loader
├── run.py                       # one-command dev launcher
└── docker-compose.yml
```

<br/>

## 🚀 Running It Locally

### ⚡ Quickest — one command
*(needs Python 3 + Node.js installed)*

```bash
python run.py
```
Sets up both backend and frontend, starts both, and prints the dashboard URL
(`http://localhost:5173`) once ready. `Ctrl+C` stops everything.

### 🔧 Manually

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

<br/>

## ☁️ Deployment

<table>
<tr>
<td valign="top" width="50%">

### 🟢 Backend — Render

| Setting | Value |
|---|---|
| Root Directory | `icc-app` |
| Build Command | `pip install -r backend/requirements.txt` |
| Start Command | `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT` |

</td>
<td valign="top" width="50%">

### ▲ Frontend — Vercel

| Setting | Value |
|---|---|
| Root Directory | `frontend` |
| Framework | Vite *(auto-detected)* |
| Env Variable | `VITE_API_URL` = `<render-url>/api` |

</td>
</tr>
</table>

<br/>

---

<div align="center">

### 📄 License

Built for educational/portfolio purposes. Underlying cricket data belongs to
its original sources; this project only reshapes it for analysis.

<br/>

**[🔗 icc-analysis.vercel.app](https://icc-analysis.vercel.app/)**

</div>
