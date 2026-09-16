"""
Cleans the ODI Cricket World Cup source: 13 per-year Excel workbooks
(1975-2023), each with a 'Results' sheet (match-by-match) and one or more
group/points-table sheets. This is the cleanest source for ODI WC match data
(vs. the corrupted ball-by-ball export and the team-innings-only icc_cwc.csv),
so it's the backbone for this tournament.
"""
import pandas as pd
import glob
import re
from pathlib import Path

RAW = Path(__file__).resolve().parents[1] / "data" / "raw" / "archive__9_"
OUT = Path(__file__).resolve().parents[1] / "data" / "processed"
OUT.mkdir(parents=True, exist_ok=True)

matches_all = []
standings_all = []

for f in sorted(glob.glob(str(RAW / "*_WC_matches.xlsx"))):
    year = int(re.match(r"(\d{4})", Path(f).name).group(1))
    xls = pd.ExcelFile(f)

    res = xls.parse("Results")
    res["year"] = year
    matches_all.append(res)

    for sheet in xls.sheet_names:
        if sheet == "Results":
            continue
        tbl = xls.parse(sheet)
        # Column naming is inconsistent across years ('Team', 'Column1', 'Teams.2') -
        # the team name is always the first column, so normalize it positionally.
        tbl = tbl.rename(columns={tbl.columns[0]: "team"})
        tbl["year"] = year
        tbl["stage"] = sheet
        standings_all.append(tbl)

matches = pd.concat(matches_all, ignore_index=True)
matches.columns = [c.strip().lower().replace(" ", "_") for c in matches.columns]
matches = matches.rename(columns={
    "team_1": "team1", "team_2": "team2",
    "team_1_score": "team1_score", "team_1_wickets": "team1_wickets", "team_1_overs": "team1_overs",
    "team_2_score": "team2_score", "team_2_wickets": "team2_wickets", "team_2_overs": "team2_overs",
    "win_margin": "win_margin",
})
matches["match_date"] = pd.to_datetime(matches["match_date"], errors="coerce")
matches["match_id"] = "ODIWC-" + matches["year"].astype(str) + "-" + matches["match_number"].astype("Int64").astype(str)
col_order = ["match_id", "year", "stage", "match_number", "match_date", "ground", "country",
             "team1", "team1_score", "team1_wickets", "team1_overs",
             "team2", "team2_score", "team2_wickets", "team2_overs",
             "winner", "win_margin", "toss"]
matches = matches[[c for c in col_order if c in matches.columns]].sort_values(["year", "match_number"])
matches.to_csv(OUT / "odi_wc_matches.csv", index=False)

standings = pd.concat(standings_all, ignore_index=True)
standings.columns = [str(c).strip().lower().replace(" ", "_").replace("/", "_") for c in standings.columns]
# Drop any stray "teams.1"/"teams.2" duplicate-header artifact columns picked up from
# merged-cell headers in a couple of the source sheets; the real team name already
# lives in the normalized 'team' column.
standings = standings[[c for c in standings.columns if not re.match(r"^teams?\.\d+$|^column\d+$", c)]]
standings = standings.dropna(subset=["team"])
standings.to_csv(OUT / "odi_wc_standings.csv", index=False)

print(f"ODI WC matches: {matches.shape}, standings: {standings.shape}")
print(matches.year.value_counts().sort_index())
