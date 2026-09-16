# Architecture

## Data flow

```
data/raw/ (10 untouched sources)
   │
   ├─ 01_data_audit.py        → data_audit_summary.csv (shape of every raw file)
   ├─ 02_clean_odi_wc.py      → odi_wc_matches.csv, odi_wc_standings.csv
   ├─ 03_clean_t20_wc.py      → t20_wc_matches.csv, t20_wc_players.csv, t20_wc_editions.csv,
   │                             t20_wc_{most_runs,most_wickets,best_bowling,highest_totals,lowest_totals}.csv
   ├─ 04_clean_champions_trophy.py → champions_trophy_matches.csv, champions_trophy_players.csv
   ├─ 05_clean_wtc.py         → wtc_matches.csv, wtc_points_tables.csv, wtc_venues.csv,
   │                             wtc_records.csv, wtc_{batting,bowling}_stats_2019_2021.csv
   ├─ 06_build_editions.py    → tournament_editions.csv (master, all 4 formats)
   └─ 08_validate_data.py     → validation_report.txt
         │
         ▼
data/processed/ (20 analytics-ready CSVs)
         │
         ▼
backend/app/main.py (FastAPI, reads CSVs directly with pandas)
         │
         ▼
frontend/src/main.jsx (React/Vite, fetches /api/*)
```

The live app never touches a database - `backend/app/main.py` reads the processed CSVs
directly with pandas on every request (they're small enough - largest is ~80KB). Postgres
(`database/schema.sql` + `scripts/07_load_database.py`) is an optional path for anyone who
wants to query the same data with SQL instead.

## Why 4 separate match tables instead of 1 unified one

ODI WC, T20 WC, Champions Trophy and WTC each track genuinely different things per match
(overs/wickets for limited-overs, result-type/summary for Tests, team batting/bowling
rankings for T20 WC & CT). Forcing them into one lowest-common-denominator schema would
lose real signal (e.g. WTC has no "score", only a result and a Wisden-style summary
string). The API exposes them uniformly at the *route* level (`/api/{fmt}/matches`,
`/api/{fmt}/teams`, etc. all take the same shape of query params and return comparably
shaped team-stats), while keeping each format's actual columns underneath.

## Known gaps (see README's "Data quality notes" for the full list)

- No per-player stats exist for Champions Trophy in the source data.
- WTC per-player batting/bowling stats: 2019-21 has a full roster (207 players);
  2021-23 and 2023-25 only have leaderboard-sized cuts (50/48 and 10/10 respectively -
  see scripts/05_clean_wtc.py and data/raw/gap_fill_2026-09-14/wtc_player_stats/ for why
  the 2023-25 cut specifically is smaller than what was attempted). All 3 feed
  /api/overview/key-players; none are exposed as a browsable Squads page for WTC, since
  2021-23/2023-25 aren't full rosters and would misrepresent that cycle's actual squad
  depth if shown as if they were.
- A large ball-by-ball ODI archive (`data/raw/archive__12_/`) is not wired into the
  pipeline - it's a good candidate for a deeper follow-up project.
