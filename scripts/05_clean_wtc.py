"""
Cleans and combines the World Test Championship sources across all three
completed cycles (2019-21, 2021-23, 2023-25). The 2019-21 cycle (archive_13 /
archive_14) is a much deeper Statsguru-style export (per-player batting/
bowling averages, partnerships, rankings) than the other two cycles' raw
folders, which only ship top-5 leaderboard-style Records.csv files - so every
cycle's top-5 leaderboards still go into the shared `wtc_records` table below
(the UI's per-cycle Records view), regardless of source depth.

A 2026-09-14 gap-fill batch (data/raw/gap_fill_2026-09-14/wtc_player_stats/,
see VERIFICATION_NOTES.md there) added real per-player batting/bowling stats
for 2021-23 and 2023-25 too, so `wtc_batting/bowling_stats_{cycle}.csv` now
exist for all 3 cycles and are used by the /api/overview/key-players endpoint
(backend/app/main.py). They are still NOT exposed as a browsable "Squads"
page, though, unlike the other 3 formats - 2019-21's files cover a genuinely
complete roster (207 players), while 2021-23/2023-25's are leaderboard cuts
(50/48 and 10/10 respectively, not every player who featured that cycle), so
showing them as if they were equivalent full squad lists would misrepresent
the two newer cycles' actual squad depth.
"""
import pandas as pd
import re
from pathlib import Path


def parse_wtc_date_range(s):
    """Parses the raw WTC folders' 'Match_Date' strings, e.g. '4-8 Aug 2021' or the
    cross-month form '29 Nov-3 Dec 2021', into the range's start date. A plain
    pd.to_datetime call misreads these as garbage (wrong month/day, spurious time
    component) since they're a day-range + single trailing month/year, not a single date."""
    if not isinstance(s, str):
        return pd.NaT
    m = re.match(r"^(\d{1,2})\s*([A-Za-z]{3})?-\d{1,2}\s*([A-Za-z]{3})?\s+(\d{4})$", s.strip())
    if not m:
        return pd.NaT
    day, mon1, mon2, year = m.groups()
    month = mon1 or mon2
    try:
        return pd.to_datetime(f"{day} {month} {year}", format="%d %b %Y")
    except Exception:
        return pd.NaT

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
OUT = Path(__file__).resolve().parents[1] / "data" / "processed"

CYCLES = {
    "2019-2021": RAW / "archive__13_",
    "2021-2023": RAW / "WTC_2021-2023_Dataset",
    "2023-2025": RAW / "WTC_2023-2025_Dataset",
}

# --- Matches: normalize the two different schemas into one common shape ---
matches_all = []

# 2019-21 (archive_13) schema: Match_No, Scorecard, Match_Date, Ground, Match, Winner,
# Margin, Match Days, Country (host), Opposition, Ground_full_Name
d = pd.read_csv(CYCLES["2019-2021"] / "(1) Matches.csv")
d["cycle"] = "2019-2021"
d["match_date"] = pd.to_datetime(d["Match_Date"], errors="coerce")
d = d.rename(columns={"Country": "host_country", "Match": "match", "Winner": "winner",
                       "Margin": "result_summary", "Match_No": "match_no"})
d["series"] = None
d["result_type"] = d["winner"].map(lambda w: "Draw" if w == "drawn" else "Win")
matches_all.append(d[["cycle", "match_no", "match_date", "Ground", "host_country", "match",
                       "result_type", "winner", "result_summary", "series"]]
                    .rename(columns={"Ground": "ground"}))

# 2021-23 / 2023-25 (raw WTC folders) schema: Match_No, Series, Match_Date, Ground,
# Host_Country, Match, Result_Type, Winner, Result_Summary, Points
import csv as _csv
for cycle in ["2021-2023", "2023-2025"]:
    # Both pandas engines throw a false "Expected N fields" error on these two files even
    # though every row has a consistent, correctly-quoted field count (verified with the
    # stdlib csv module) - reading via csv.reader directly sidesteps whatever trips their
    # tokenizers.
    with open(CYCLES[cycle] / "Matches.csv", newline="", encoding="utf-8") as fh:
        rows = list(_csv.reader(fh))
    header, body = rows[0], rows[1:]
    # A few 2023-25 Result_Summary values contain an unescaped mid-sentence comma
    # ("...Match drawn, rain-affected)..."), producing one extra field - rejoin the
    # Result_Summary column (2nd-to-last) with its overflow neighbour before framing.
    fixed = []
    for r in body:
        while len(r) > len(header):
            r = r[:8] + [r[8] + "," + r[9]] + r[10:]
        fixed.append(r)
    d = pd.DataFrame(fixed, columns=header)
    d["cycle"] = cycle
    d["match_date"] = d["Match_Date"].map(parse_wtc_date_range)
    d = d.rename(columns={"Match_No": "match_no", "Ground": "ground", "Host_Country": "host_country",
                           "Match": "match", "Result_Type": "result_type", "Winner": "winner",
                           "Result_Summary": "result_summary", "Series": "series"})
    matches_all.append(d[["cycle", "match_no", "match_date", "ground", "host_country", "match",
                           "result_type", "winner", "result_summary", "series"]])

matches = pd.concat(matches_all, ignore_index=True)
matches[["team1", "team2"]] = matches["match"].str.split(" v ", n=1, expand=True)
matches["match_id"] = "WTC-" + matches["cycle"] + "-" + matches["match_no"].astype(str)
matches = matches[["match_id", "cycle", "match_no", "series", "match_date", "ground", "host_country",
                    "team1", "team2", "result_type", "winner", "result_summary"]]
matches.to_csv(OUT / "wtc_matches.csv", index=False)

# --- Points tables (final league standings per cycle) ---
pt_all = []
d = pd.read_csv(CYCLES["2019-2021"] / "(7) Points Table.csv")
d = d.rename(columns={"Country": "team", "Series Played": "series_played", "Series Won": "series_won",
                       "Matches": "matches", "Won": "won", "Lost": "lost", "Tied": "tied", "Draw": "draw",
                       "Points": "points", "Runs/wkt rate": "pct", "Current ICC Ranking": "final_position"})
d = d.sort_values("final_position")
d["cycle"] = "2019-2021"
pt_all.append(d[["cycle", "team", "matches", "won", "lost", "tied", "draw", "points", "pct", "final_position"]])
for cycle in ["2021-2023", "2023-2025"]:
    d = pd.read_csv(CYCLES[cycle] / "Points Table.csv")
    d = d.rename(columns={"Pos": "final_position", "Team": "team", "Pld": "matches", "W": "won", "L": "lost",
                           "D": "draw", "T": "tied", "PCT": "pct", "Pts": "points"})
    d["cycle"] = cycle
    pt_all.append(d[["cycle", "team", "matches", "won", "lost", "tied", "draw", "points", "pct", "final_position"]])
points_tables = pd.concat(pt_all, ignore_index=True).sort_values(["cycle", "final_position"])
points_tables.to_csv(OUT / "wtc_points_tables.csv", index=False)

# --- Venues ---
v_all = []
d = pd.read_csv(CYCLES["2019-2021"] / "(11) WTC_Venues.csv")
d = d.rename(columns={"Ground": "ground", "Mat": "matches_hosted", "Country": "country"})
d["cycle"] = "2019-2021"
v_all.append(d[["cycle", "ground", "matches_hosted", "country"]])
for cycle in ["2021-2023", "2023-2025"]:
    d = pd.read_csv(CYCLES[cycle] / "WTC_Venues.csv")
    d = d.rename(columns={"Ground": "ground", "Matches_Hosted": "matches_hosted", "Country": "country"})
    d["cycle"] = cycle
    v_all.append(d[["cycle", "ground", "matches_hosted", "country"]])
venues = pd.concat(v_all, ignore_index=True)
venues.to_csv(OUT / "wtc_venues.csv", index=False)

# --- Records: top-5 leaderboards, all 3 cycles in one long table ---
# 2021-23 and 2023-25 each ship a ready-made Records.csv (12 categories + Prize Money).
# 2019-21 (archive_13) has no single equivalent file - its leaderboard data is spread
# across separate per-player exports (batting, bowling, wicketkeeping, fielding, plus
# curated highest-team-total/match-aggregate/partnership lists), so this builds an
# equivalent top-5-style table from those instead of leaving the cycle out. 5 categories
# come from files that were already curated top-N lists (Most Runs/Wickets, Highest Team
# Total/Match Aggregate/Partnership); a further 7 are computed directly from the raw
# per-player season stats below, bringing 2019-21 to the same 12 categories as the other
# two cycles (see the "gap-fill" block after the initial records concat for why 2 of the
# 2021-23/2023-25 categories - Lowest Team Total, Highest Successful Chase - could not be
# added for 2019-21 without fabricating numbers this cycle's raw export doesn't contain).
rec_all = []
for cycle in ["2021-2023", "2023-2025"]:
    d = pd.read_csv(CYCLES[cycle] / "Records.csv")
    d.columns = [c.strip().lower().replace("/", "_") for c in d.columns]
    d["cycle"] = cycle
    rec_all.append(d)

d19 = CYCLES["2019-2021"]

def top5(df, rank_col, player_col, detail_fn, value_col, category, ascending=False):
    top = df.sort_values(rank_col, ascending=ascending).head(5).reset_index(drop=True)
    return pd.DataFrame({
        "cycle": "2019-2021", "category": category, "rank": range(1, len(top) + 1),
        "player_team": top[player_col], "detail": top.apply(detail_fn, axis=1), "value": top[value_col],
    })

bat19 = pd.read_csv(d19 / "(2) batting_runs.csv")
rec_all.append(top5(bat19, "Runs", "Player", lambda r: f"{r.Mat} Mat, {r.Inns} Inn, HS {r.HS}", "Runs", "Most Runs"))

bowl19 = pd.read_csv(d19 / "(3) Bowling.csv")
bowl19 = bowl19[bowl19.Wkts > 0]
rec_all.append(top5(bowl19, "Wkts", "Player", lambda r: f"{r.Inns} Inn, BBI {r.BBI}, BBM {r.BBM}", "Wkts", "Most Wickets"))

hi_tot = pd.read_csv(d19 / "(7) hghst_inn_tot.csv")
rec_all.append(top5(hi_tot, "Score", "Country", lambda r: f"{r.Overs} overs, {r.Scorecard}", "Score", "Highest Team Total"))

hi_agg = pd.read_csv(d19 / "(7) hghst_mat_aggrt.csv")
rec_all.append(top5(hi_agg, "Runs", "Country", lambda r: f"vs {r.Opposition}, {r.Wkts} wkts, {r.Scorecard}", "Runs", "Highest Match Aggregate"))

part19 = pd.read_csv(d19 / "(5) Highest Partnership.csv")
rec_all.append(top5(part19, "Runs", "Partners", lambda r: f"{r.Wkt} wkt vs {r.Opposition}, {r.Scorecard}", "Runs", "Highest Partnership"))

records = pd.concat(rec_all, ignore_index=True)
records = records[["cycle", "category", "rank", "player_team", "detail", "value"]]

# --- 2019-21 gap-fill: 7 more categories that ARE derivable from this cycle's raw
# per-player exports, bringing it in line with the 12 leaderboard categories the other
# two cycles have (Prize Money is cycle-specific prize-pool data, not a performance
# record, and was never part of 2019-21's set anyway). Two categories are NOT filled in
# here because the source data genuinely can't support them without fabricating numbers:
#   - "Lowest Team Total": (7) hghst_inn_tot.csv is a curated top-50 *highest* list, not
#     every innings played, so its lowest entries are not the cycle's actual lowest totals.
#   - "Highest Successful Chase": (1) Matches.csv only has text margins like "6 wickets",
#     with no actual target/runs-chased figure to rank by.
# Both would need a full match-by-match innings scorecard export that this cycle's raw
# data doesn't include, unlike 2021-23/2023-25's ready-made Records.csv.

def parse_figures(s):
    """'10/119' -> (10, 119) - wickets then runs conceded, for BBI/BBM sorting (more
    wickets is better; among equal wickets, fewer runs conceded is better)."""
    w, r = str(s).split("/")
    return int(w), int(r)

def balls_from_overs(v):
    """Overs are stored in cricket's ball-notation (630.5 = 630 overs + 5 balls, not
    630.5 decimal overs) - a plain float read would under/overcount the fractional part."""
    whole = int(v)
    return whole * 6 + round((v - whole) * 10)

def add19(category, rows, detail_col_fn, value_fn=lambda r: r["_value"]):
    top = rows.head(5).reset_index(drop=True)
    return pd.DataFrame({
        "cycle": "2019-2021", "category": category, "rank": range(1, len(top) + 1),
        "player_team": top["Player"], "detail": top.apply(detail_col_fn, axis=1), "value": top.apply(value_fn, axis=1),
    })

fill19 = []

bat19_full = pd.read_csv(d19 / "(2) batting_runs.csv")
bat19_full = bat19_full[bat19_full["Inns"] > 0].copy()  # drop the "-" HS rows (never batted)
bat19_full["_hs_num"] = bat19_full["HS"].str.replace("*", "", regex=False).astype(int)
hs_top = bat19_full.sort_values("_hs_num", ascending=False)
fill19.append(add19("Highest Individual Score", hs_top,
                     lambda r: f"{r.Mat} Mat, {r.Inns} Inn", lambda r: r.HS))

bat19_avg = bat19_full[bat19_full["Inns"] >= 10].copy()
denom = (bat19_avg["Inns"] - bat19_avg["NO"]).astype(float)
bat19_avg["_avg"] = (bat19_avg["Runs"] / denom.where(denom != 0)).round(2)
bat19_avg = bat19_avg.sort_values("_avg", ascending=False)
fill19.append(add19("Highest Batting Average (min 10 inn)", bat19_avg,
                     lambda r: f"{r.Mat} Mat, {r.Inns} Inn, {r.Runs} runs, HS {r.HS}", lambda r: r["_avg"]))

bowl19_full = pd.read_csv(d19 / "(3) Bowling.csv")
bowl19_full = bowl19_full[bowl19_full["Wkts"] > 0].copy()
bowl19_full[["_bbi_w", "_bbi_r"]] = bowl19_full["BBI"].apply(lambda s: pd.Series(parse_figures(s)))
bowl19_full[["_bbm_w", "_bbm_r"]] = bowl19_full["BBM"].apply(lambda s: pd.Series(parse_figures(s)))
bbi_top = bowl19_full.sort_values(["_bbi_w", "_bbi_r"], ascending=[False, True])
fill19.append(add19("Best Bowling (Innings)", bbi_top,
                     lambda r: f"{r.Inns} Inn, career {r.Wkts} wkts", lambda r: r.BBI))
bbm_top = bowl19_full.sort_values(["_bbm_w", "_bbm_r"], ascending=[False, True])
fill19.append(add19("Best Bowling (Match)", bbm_top,
                     lambda r: f"{r.Inns} Inn, career {r.Wkts} wkts", lambda r: r.BBM))

bowl19_full["_balls"] = bowl19_full["Overs"].apply(balls_from_overs)
bowl19_avg = bowl19_full[bowl19_full["_balls"] >= 500].copy()
bowl19_avg["_avg"] = (bowl19_avg["Runs"] / bowl19_avg["Wkts"].astype(float)).round(2)
bowl19_avg = bowl19_avg.sort_values("_avg", ascending=True)
fill19.append(add19("Best Bowling Average (min 500 balls)", bowl19_avg,
                     lambda r: f"{r.Inns} Inn, {r.Wkts} Wkts, BBI {r.BBI}, BBM {r.BBM}", lambda r: r["_avg"]))

wk19 = pd.read_csv(d19 / "(4) WK.csv")
wk19["_dismissals"] = wk19["St"] + wk19["Ct Wk"]
wk19 = wk19.sort_values("_dismissals", ascending=False)
fill19.append(add19("Most Dismissals (WK)", wk19,
                     lambda r: f"{r.Inns} Inn, {r['Ct Wk']} Ct, {r.St} St", lambda r: r["_dismissals"]))

field19 = pd.read_csv(d19 / "(4) fielding.csv")
field19 = field19.sort_values("Ct Fi", ascending=False)
fill19.append(add19("Most Catches (Fielder)", field19,
                     lambda r: f"{r.Inns} Inn", lambda r: r["Ct Fi"]))

records = pd.concat([records] + fill19, ignore_index=True)
records.to_csv(OUT / "wtc_records.csv", index=False)

# --- Player stats: 2019-21 cycle only (the only cycle with a full export). Written to
# data/processed/ but intentionally not served by the API/UI - see module docstring. ---
# Source has no separate team column (it's embedded in Player as "Name (TEAM)") and no
# average column - both are derived here rather than left for the frontend to compute.
def split_team(player):
    m = re.match(r"^(.*)\((\w+)\)\s*$", str(player).strip())
    return (m.group(1).strip(), m.group(2)) if m else (player, None)

bat = pd.read_csv(CYCLES["2019-2021"] / "(2) batting_runs.csv")
bat.columns = [c.strip().lower().replace("%", "pct") for c in bat.columns]
bat[["player", "team"]] = bat["player"].apply(lambda p: pd.Series(split_team(p)))
denom = (bat["inns"] - bat["no"]).astype(float)
bat["avg"] = (bat["runs"] / denom.where(denom != 0)).round(2)
bat["cycle"] = "2019-2021"
bat.to_csv(OUT / "wtc_batting_stats_2019_2021.csv", index=False)

bowl = pd.read_csv(CYCLES["2019-2021"] / "(3) Bowling.csv")
bowl.columns = [c.strip().lower() for c in bowl.columns]
bowl[["player", "team"]] = bowl["player"].apply(lambda p: pd.Series(split_team(p)))
wkts_f = bowl["wkts"].astype(float)
bowl["avg"] = (bowl["runs"] / wkts_f.where(wkts_f != 0)).round(2)
bowl["cycle"] = "2019-2021"
bowl.to_csv(OUT / "wtc_bowling_stats_2019_2021.csv", index=False)

print(f"WTC matches: {matches.shape}, points_tables: {points_tables.shape}, "
      f"venues: {venues.shape}, records: {records.shape}, batting: {bat.shape}, bowling: {bowl.shape}")
print(matches.cycle.value_counts())

# --- Player stats: 2021-23 and 2023-25 gap-fill (2026-09-14) ---
# 2019-21 used to be "the only cycle with a full [batting/bowling] export" (see module
# docstring above, now stale) - these two gap-fill batches close that for the other two
# cycles, bringing every cycle's per-player batting/bowling stats up to the same shape.
# See data/raw/gap_fill_2026-09-14/wtc_player_stats/VERIFICATION_NOTES.md for the full
# story: the 2021-23 files were spot-checked against this project's own already-verified
# records and passed cleanly, so they're loaded as delivered. The 2023-25 files did NOT
# pass verification (a row marked "confirmed" disagreed with independently-sourced data
# on 5 separate fields at once, on top of the 2 issues the source README itself flagged),
# so that cycle's stats are rebuilt below from scratch, from independently corroborated
# web sources instead of the uploaded numbers - a smaller top-10/top-10 cut rather than
# the uploaded top-20/top-10, but every row here has been cross-checked, not scraped.
GAP19 = Path(__file__).resolve().parents[1] / "data" / "raw" / "gap_fill_2026-09-14" / "wtc_player_stats"

bat21 = pd.read_csv(GAP19 / "batting_2021_2023.csv")
bat21 = bat21.rename(columns={"ave": "avg", "player": "player"})
bat21["cycle"] = "2021-2023"
bat21.to_csv(OUT / "wtc_batting_stats_2021_2023.csv", index=False)

bowl21 = pd.read_csv(GAP19 / "bowling_2021_2023.csv")
bowl21 = bowl21.rename(columns={"ave": "avg"})
bowl21["cycle"] = "2021-2023"
bowl21.to_csv(OUT / "wtc_bowling_stats_2021_2023.csv", index=False)

# 2023-25 top 10 batters, verified against Business Standard's ESPNcricinfo-sourced
# table (https://www.business-standard.com/cricket/news/full-list-of-highest-run-getters
# -in-world-test-championship-2023-25-cycle-125060900877_1.html, 11 Jun 2025) - every
# field below (Mat/Inns/NO/Runs/HS/Ave/BF/SR/100/50/0/4s/6s) matches that table exactly.
bat23_rows = [
    ("JE Root", "ENG", "2023-2024", 22, 40, 4, 1968, "262", 54.66, 3006, 65.46, 7, 7, 1, 186, 9),
    ("YBK Jaiswal", "IND", "2023-2025", 19, 36, 2, 1798, "214*", 52.88, 2738, 65.66, 4, 10, 3, 207, 39),
    ("BM Duckett", "ENG", "2023-2024", 22, 41, 1, 1470, "153", 36.75, 1743, 84.33, 2, 8, 2, 187, 7),
    ("HC Brook", "ENG", "2023-2024", 17, 29, 0, 1463, "317", 50.44, 1755, 83.36, 4, 7, 1, 144, 17),
    ("UT Khawaja", "AUS", "2023-2025", 19, 37, 3, 1422, "232", 41.82, 3168, 44.88, 2, 6, 2, 149, 5),
    ("SPD Smith", "AUS", "2023-2025", 19, 35, 3, 1324, "141", 41.37, 2549, 51.94, 5, 4, 2, 133, 11),
    ("TM Head", "AUS", "2023-2025", 19, 34, 1, 1177, "152", 35.66, 1452, 81.06, 3, 5, 4, 151, 13),
    ("Z Crawley", "ENG", "2023-2024", 19, 34, 0, 1175, "189", 34.55, 1509, 77.86, 1, 8, 3, 152, 10),
    ("KS Williamson", "NZ", "2023-2024", 11, 22, 1, 1152, "156", 54.85, 2128, 54.13, 5, 4, 1, 134, 6),
    ("PHKD Mendis", "SL", "2024-2025", 11, 20, 2, 1123, "182*", 62.38, 1702, 65.98, 5, 3, 0, 116, 23),
]
bat23 = pd.DataFrame(bat23_rows, columns=["player", "team", "span", "mat", "inns", "no", "runs", "hs",
                                           "avg", "bf", "sr", "100", "50", "0", "4s", "6s"])
bat23["cycle"] = "2023-2025"
bat23.to_csv(OUT / "wtc_batting_stats_2023_2025.csv", index=False)

# 2023-25 top 10 bowlers, verified against 2 independent sources (khelnow.com and
# cricketcountry.com's post-final wrap-ups, both 14-15 Jun 2025) agreeing on every name,
# wicket count and match count - this is also where Starc's real 77 (not 71) comes from.
bowl23_rows = [
    ("PJ Cummins", "AUS", "2023-2025", 18, 35, 563.5, 76, 1879, 80, "6/28", 23.48, 3.33, 42.28),
    ("JJ Bumrah", "IND", "2023-2025", 15, 28, 393.4, 91, 1162, 77, "6/45", 15.09, 2.95, 30.67),
    ("MA Starc", "AUS", "2023-2025", 19, 37, 538.0, 81, 2071, 77, "6/48", 26.89, 3.84, 41.92),
    ("NM Lyon", "AUS", "2023-2025", 17, 30, 546.5, 76, 1662, 66, "6/65", 25.18, 3.03, 49.71),
    ("R Ashwin", "IND", "2023-2024", 14, 26, 445.3, 61, 1547, 63, "7/71", 24.55, 3.47, 42.42),
    ("JR Hazlewood", "AUS", "2023-2025", 16, 29, 420.0, 90, 1204, 59, "5/45", 20.41, 2.87, 42.71),
    ("MDK Jayasuriya", "SL", "2023-2025", 12, 22, 367.1, 79, 2131, 58, "6/42", 36.74, 3.48, 63.29),
    ("K Rabada", "SA", "2023-2025", 11, 21, 330.3, 64, 1049, 56, "6/46", 18.73, 3.17, 35.41),
    ("RA Jadeja", "IND", "2023-2025", 15, 26, 418.1, 70, 1289, 55, "5/41", 23.43, 3.08, 45.61),
    ("GL Atkinson", "ENG", "2024-2024", 11, 21, 308.4, 52, 1152, 52, "7/45", 22.15, 3.73, 35.61),
]
bowl23 = pd.DataFrame(bowl23_rows, columns=["player", "team", "span", "mat", "inns", "overs", "mdns",
                                             "runs", "wkts", "bbi", "avg", "econ", "sr"])
bowl23["cycle"] = "2023-2025"
bowl23.to_csv(OUT / "wtc_bowling_stats_2023_2025.csv", index=False)

# --- wtc_records.csv corrections (see VERIFICATION_NOTES.md) ---
records = pd.read_csv(OUT / "wtc_records.csv")
j_mask = (records.cycle == "2023-2025") & (records.category == "Most Runs") & (records.player_team.str.contains("Jaiswal"))
records.loc[j_mask, "value"] = "1798"
s_mask = (records.cycle == "2023-2025") & (records.category == "Most Wickets") & (records.player_team.str.contains("Starc"))
records.loc[s_mask, "value"] = "77"
# A third, pre-existing error found incidentally while verifying the above two: this
# cycle's "Most Runs" rank-5 (Khawaja) was already wrong in wtc_records.csv before this
# gap-fill batch, independent of today's upload - built from the same flawed underlying
# numbers. Corrected against the same verified Business Standard table used for the
# 2023-25 batting rebuild above (19 Mat, 37 Inn, 1422 runs, Ave 41.82 - HS 232 was
# already correct).
k_mask = (records.cycle == "2023-2025") & (records.category == "Most Runs") & (records.player_team.str.contains("Khawaja"))
records.loc[k_mask, "detail"] = "19 Mat, 37 Inn, 3 NO, Avg 41.82, HS 232"
records.loc[k_mask, "value"] = "1422"
records.to_csv(OUT / "wtc_records.csv", index=False)

print(f"WTC player stats gap-fill: 2021-23 batting {bat21.shape}, bowling {bowl21.shape}; "
      f"2023-25 batting {bat23.shape}, bowling {bowl23.shape}. "
      f"Corrected {j_mask.sum()} Jaiswal, {s_mask.sum()} Starc, {k_mask.sum()} Khawaja row(s) in wtc_records.csv.")
