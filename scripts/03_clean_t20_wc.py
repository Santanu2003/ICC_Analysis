"""
Cleans the T20 World Cup sources: match results with scores + team rankings
(wc_final_dataset.xlsx - richer than the plain results CSV, so used as
primary), full player lists per edition, and the top-5 all-time records
(most runs/wickets, best bowling, highest/lowest totals).
"""
import pandas as pd
from pathlib import Path

RAW10 = Path(__file__).resolve().parents[1] / "data" / "raw" / "archive__10_"
RAW11 = Path(__file__).resolve().parents[1] / "data" / "raw" / "archive__11_"
OUT = Path(__file__).resolve().parents[1] / "data" / "processed"

# --- Matches ---
m = pd.read_excel(RAW10 / "wc_final_dataset.xlsx")
m.columns = [c.strip().lower().replace(" ", "_").replace("-", "_") for c in m.columns]
m["match_date"] = pd.to_datetime(m["match_date"], errors="coerce")
m["year"] = m["match_date"].dt.year
# The 2021 and 2022 editions ran Oct-Nov of their year but organizers/records treat them
# as those years already, so no edition-boundary correction is needed here.
m = m.sort_values("match_date").reset_index(drop=True)
m["match_id"] = "T20WC-" + m["year"].astype(str) + "-" + (m.index + 1).astype(str)
cols = ["match_id", "year", "match_date", "team1", "team2", "winner",
        "team1_score", "team2_score", "margin", "ground", "host_country",
        "t_20_int_match", "team1_avg_batting_ranking", "team2_avg_batting_ranking",
        "team1_avg_bowling_ranking", "team2_avg_bowling_ranking",
        "team1_total_wcs_participated", "team1_total_wcs_won",
        "team2_total_wcs_participated", "team2_total_wcs_won", "team1_win_%_over_team2"]
m = m[[c for c in cols if c in m.columns]]
m = m.rename(columns={"t_20_int_match": "match_no", "team1_win_%_over_team2": "team1_win_pct_over_team2"})
m.to_csv(OUT / "t20_wc_matches.csv", index=False)

# --- Players ---
p = pd.read_csv(RAW10 / "all_t20_world_cup_players_list.csv")
p.columns = ["team", "year", "player_name"]
p.to_csv(OUT / "t20_wc_players.csv", index=False)

# --- Records (5 small top-lists; keep separate, each is a distinct stat shape) ---
for name in ["most_runs", "most_wickets", "best_bowling", "highest_totals", "lowest_totals"]:
    d = pd.read_csv(RAW11 / f"{name}.csv")
    # Each file's last row is a footnote ("Qualification: ... Last updated ...") repeated
    # across every column rather than real data - drop it by content, not length (several
    # real score/date values here run longer than any reasonable length cutoff).
    first_col = d.columns[0]
    is_footnote = d[first_col].astype(str).str.contains("Qualification|Last updated", case=False, na=False)
    d = d[~is_footnote]
    d.to_csv(OUT / f"t20_wc_{name}.csv", index=False)

# --- Finals summary (winner/runner-up by year, doubles as edition list) ---
t = pd.read_csv(RAW11 / "tournament_summary.csv")
t = t.dropna(subset=["Winner"])
t.columns = ["year", "winner", "winner_score", "runner_up", "runner_up_score", "ref"]
t = t.drop(columns=["ref"])
t.to_csv(OUT / "t20_wc_editions.csv", index=False)

print(f"T20 WC matches: {m.shape}, players: {p.shape}, editions: {t.shape}")
print(m.year.value_counts().sort_index())
