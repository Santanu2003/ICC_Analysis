"""
Builds one master 'editions' table across all 4 ICC tournament formats,
mirroring the FIFA project's wc_editions file. ODI WC / T20 WC / Champions
Trophy editions come straight from the bundled master spreadsheet. WTC has no
such summary in the source data, so its 3 completed-cycle winners/runners-up
are derived here from wtc_matches (the final is each cycle's last-played
match) cross-checked against wtc_points_tables.
"""
import pandas as pd
from pathlib import Path

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
OUT = Path(__file__).resolve().parents[1] / "data" / "processed"

master = pd.read_excel(RAW / "archive__6_" / "icc_dataset.xlsx")
master.columns = [c.strip().lower().replace(" ", "_").replace("-", "_") for c in master.columns]
master = master.rename(columns={"match_winner_final": "final_player_of_match"})
master["cycle"] = None

# WTC finals: for each cycle, the final is the last chronologically-played match whose
# two teams also occupy the top two final_position spots in that cycle's points table
# (distinguishes it from unrelated bilateral Tests that happened to finish the same week).
wtc_matches = pd.read_csv(OUT / "wtc_matches.csv", parse_dates=["match_date"])
wtc_points = pd.read_csv(OUT / "wtc_points_tables.csv")

wtc_rows = []
for cycle, grp in wtc_matches.groupby("cycle"):
    top2 = set(wtc_points[(wtc_points.cycle == cycle) & (wtc_points.final_position <= 2)].team)
    finals = grp[(grp.team1.isin(top2)) & (grp.team2.isin(top2))].sort_values("match_date")
    final = finals.iloc[-1]
    winner = final.winner if final.winner != "-" else "Drawn / shared"
    runner_up = (top2 - {winner}).pop() if winner in top2 else None
    wtc_rows.append({
        "tournament": "World Test Championship", "year": int(cycle.split("-")[1]),
        "cycle_label": cycle, "venue": final.ground, "winner": winner, "runner_up": runner_up,
        "semi_finalists": None, "final_player_of_match": None, "player_of_tournament": None,
        "cycle": cycle,
    })
wtc_editions = pd.DataFrame(wtc_rows)

editions = pd.concat([master, wtc_editions], ignore_index=True)
editions["edition_id"] = editions["tournament"].str.replace(" ", "").str.upper() + "-" + editions["year"].astype(str)
editions = editions.sort_values(["tournament", "year"])
editions.to_csv(OUT / "tournament_editions.csv", index=False)

print(editions[["tournament", "year", "winner", "runner_up"]].to_string())
