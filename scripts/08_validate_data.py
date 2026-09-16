from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "data" / "processed"
OUT = P / "validation_report.txt"
checks = []


def add(name, ok, detail):
    checks.append((name, "PASS" if ok else "FAIL", detail))


ed = pd.read_csv(P / "tournament_editions.csv")
odi_m = pd.read_csv(P / "odi_wc_matches.csv")
odi_s = pd.read_csv(P / "odi_wc_standings.csv")
t20_m = pd.read_csv(P / "t20_wc_matches.csv")
ct_m = pd.read_csv(P / "champions_trophy_matches.csv")
wtc_m = pd.read_csv(P / "wtc_matches.csv")
wtc_pt = pd.read_csv(P / "wtc_points_tables.csv")

add("Edition ID uniqueness", ed.edition_id.is_unique, f"duplicate ids={ed.edition_id.duplicated().sum()}")
add("ODI WC match ID uniqueness", odi_m.match_id.is_unique, f"dupes={odi_m.match_id.duplicated().sum()}")
add("T20 WC match ID uniqueness", t20_m.match_id.is_unique, f"dupes={t20_m.match_id.duplicated().sum()}")
add("CT match ID uniqueness", ct_m.match_id.is_unique, f"dupes={ct_m.match_id.duplicated().sum()}")
add("WTC match ID uniqueness", wtc_m.match_id.is_unique, f"dupes={wtc_m.match_id.duplicated().sum()}")

add("ODI WC every match has 2 teams", odi_m[["team1", "team2"]].notna().all(axis=1).all(),
    f"rows missing a team={(~odi_m[['team1','team2']].notna().all(axis=1)).sum()}")
add("WTC team1/team2 parsed from 'Match' column", wtc_m[["team1", "team2"]].notna().all(axis=1).all(),
    f"rows missing a team={(~wtc_m[['team1','team2']].notna().all(axis=1)).sum()}")

add("ODI WC winner is team1, team2, or a recognized no-result label", odi_m.apply(
    lambda r: r.winner in (r.team1, r.team2) or str(r.winner).strip().lower() in ("no result", "tie"), axis=1).all(),
    "winner should always resolve to a participant or a known no-result/tie label")

add("WTC points table has exactly 2 finalists per cycle in top 2", wtc_pt.groupby("cycle").apply(
    lambda g: (g.final_position <= 2).sum() == 2).all(), "each cycle's final should have exactly 2 top-2 teams")

add("WTC date range plausible (2019-2026)", wtc_m.match_date.between("2019-01-01", "2026-12-31").all(),
    f"out-of-range dates={(~wtc_m.match_date.between('2019-01-01','2026-12-31')).sum()}")

add("ODI WC edition years match the 13 known editions", set(ed[ed.tournament == "ODI World Cup"].year) == {
    1975, 1979, 1983, 1987, 1992, 1996, 1999, 2003, 2007, 2011, 2015, 2019, 2023}, "13 editions expected")

with OUT.open("w", encoding="utf-8") as f:
    for n, s, x in checks:
        f.write(f"{s}: {n} — {x}\n")
print(OUT.read_text())
