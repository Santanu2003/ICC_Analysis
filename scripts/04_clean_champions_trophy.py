"""
Cleans the Champions Trophy sources: match results (with rankings + team
head-to-head win% baked in) and full player lists per edition. No deep
per-player batting/bowling stats file exists for this tournament in the
supplied data, so this pipeline doesn't fabricate one - the frontend/API
should present CT at match + squad level only.
"""
import pandas as pd
from pathlib import Path

RAW = Path(__file__).resolve().parents[1] / "data" / "raw" / "archive__7_"
OUT = Path(__file__).resolve().parents[1] / "data" / "processed"

m = pd.read_csv(RAW / "all_champions_trophy_matches_results.csv")
m.columns = [c.strip().lower().replace(" ", "_").replace("-", "_") for c in m.columns]
m["match_date"] = pd.to_datetime(m["match_date"], errors="coerce")
m["year"] = m["match_date"].dt.year
m = m.sort_values("match_date").reset_index(drop=True)
m["match_id"] = "CT-" + m["year"].astype(str) + "-" + (m.index + 1).astype(str)
m = m.rename(columns={"odi_int_match": "match_no", "player_of_the_match": "player_of_match"})
cols = ["match_id", "year", "match_date", "team1", "team2", "toss", "winner", "margin",
        "player_of_match", "ground", "match_no",
        "team1_avg_batting_ranking", "team2_avg_batting_ranking",
        "team1_avg_bowling_ranking", "team2_avg_bowling_ranking",
        "team1_total_cts_participated", "team1_total_cts_won",
        "team2_total_cts_participated", "team2_total_cts_won", "team1_w/l_ratio_over_team2"]
m = m[[c for c in cols if c in m.columns]]
m = m.rename(columns={"team1_w/l_ratio_over_team2": "team1_wl_ratio_over_team2"})
m.to_csv(OUT / "champions_trophy_matches.csv", index=False)

p = pd.read_csv(RAW / "all_champions_trophy_players_list.csv")
p.columns = ["team", "year", "player_name"]
p.to_csv(OUT / "champions_trophy_players.csv", index=False)

print(f"Champions Trophy matches: {m.shape}, players: {p.shape}")
print(m.year.value_counts().sort_index())
