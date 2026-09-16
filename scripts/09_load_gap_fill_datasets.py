"""
GAP-FILL DATA LOAD — Sept 2026 upload.

Closes the gaps documented after the first pass of the app (see docs/DATA_SOURCES.md
"Known gaps" at the bottom) so every format — ODI World Cup, T20 World Cup, Champions
Trophy, World Test Championship — ends up with the SAME sections available:
player lists, records leaderboards, and group/league standings.

Run this after scripts 01-08 (it reads the already-processed player list files to
enrich them in place, and reads the new raw sources under
data/raw/gap_fill_2026-09-11/).

What this does, in order:
1. Builds odi_wc_players.csv — ODI World Cup had NO player-list file at all before this.
2. Builds odi_wc_records.csv / champions_trophy_records.csv, and REPLACES the old 5
   separate t20_wc_{most_runs,most_wickets,best_bowling,highest_totals,lowest_totals}.csv
   files with one t20_wc_records.csv — all four formats' records now share the exact
   same Category/Rank/Player_team/Detail/Value shape wtc_records.csv already used, so
   one generic API endpoint + one UI component renders all of them. Old T20 files are
   deleted here rather than kept alongside the new one, to avoid the same data existing
   twice in two different shapes.
3. Builds t20_wc_standings.csv / champions_trophy_standings.csv (previously only
   odi_wc had a standings file) and re-shapes odi_wc_standings.csv's columns to match,
   so /api/{fmt}/standings can be one generic endpoint for all 3 group-stage formats.
   WTC keeps its own /api/wtc/points-tables — its league/cycle scoring (Points+PCT,
   Won/Lost/Draw/Tied) is a genuinely different shape, not just a naming difference.
4. Enriches t20_wc_players.csv and champions_trophy_players.csv with DOB / nationality /
   bowling style wherever a bio match was found (~73-83% coverage — see the source
   README for exactly why the rest can't be matched from currently-available data).
5. Adds 3 small WTC-only trivia tables: finals officials, notable partnerships, umpire
   cycle-appearance counts.
6. Loads team_master / venue_master / venue_name_mapping / team_name_lookup for future
   name-normalisation use. NOT yet applied retroactively to rewrite team/venue names in
   the existing match/standings files — see docs/DATA_SOURCES.md for why that's still open.
"""
import json
import pandas as pd
from pathlib import Path

RAW = Path(__file__).resolve().parents[1] / "data" / "raw" / "gap_fill_2026-09-11"
OUT = Path(__file__).resolve().parents[1] / "data" / "processed"


# ---------------------------------------------------------------------------
# 1. ODI World Cup player list (GAP: odi_wc had no /players data at all)
# ---------------------------------------------------------------------------
def build_odi_players():
    p = pd.read_csv(RAW / "odi_wc_players_1975_2023_merged.csv")
    p = p.rename(columns={
        "Team": "team", "Year": "year", "Player": "player_name",
        "DOB": "dob", "Batting_Style": "batting_style",
        "Bowling_Style": "bowling_style", "First_Class_Team": "first_class_team",
    })
    p["bowling_style"] = p["bowling_style"].replace("-", None)
    p["first_class_team"] = p["first_class_team"].replace("-", None)
    p = p[["team", "year", "player_name", "dob", "batting_style", "bowling_style", "first_class_team"]]
    p.to_csv(OUT / "odi_wc_players.csv", index=False)
    print(f"odi_wc_players.csv: {len(p)} rows")


# ---------------------------------------------------------------------------
# 2. Records leaderboards - standardised to Category/Rank/Player_team/Detail/Value,
#    the same shape wtc_records.csv already uses.
# ---------------------------------------------------------------------------
def build_records():
    def load(fname):
        d = pd.read_csv(RAW / "records_all_tournaments" / fname)
        d.columns = ["category", "rank", "player_team", "detail", "value"]
        return d

    load("odi_wc_records.csv").to_csv(OUT / "odi_wc_records.csv", index=False)
    load("champions_trophy_records.csv").to_csv(OUT / "champions_trophy_records.csv", index=False)
    load("t20_wc_records_consolidated.csv").to_csv(OUT / "t20_wc_records.csv", index=False)

    # Superseded by t20_wc_records.csv above - remove so the data doesn't exist twice.
    for name in ["most_runs", "most_wickets", "best_bowling", "highest_totals", "lowest_totals"]:
        f = OUT / f"t20_wc_{name}.csv"
        if f.exists():
            f.unlink()
    print("records: odi_wc_records.csv, champions_trophy_records.csv, t20_wc_records.csv "
          "(old per-category t20_wc_*.csv files removed)")


# ---------------------------------------------------------------------------
# 3. Group-stage standings - one shared shape across odi_wc / t20_wc / champions_trophy.
# ---------------------------------------------------------------------------
def build_standings():
    STANDINGS_COLS = ["team", "year", "stage", "group", "pos", "m", "w", "l", "t", "n_r", "pt", "nrr", "seed"]

    def load(fname):
        d = pd.read_csv(RAW / "standings_t20_ct" / fname)
        d.columns = [c.strip().lower() for c in d.columns]
        d = d.rename(columns={"pld": "m", "nr": "n_r", "pts": "pt"})
        return d[[c for c in STANDINGS_COLS if c in d.columns]]

    load("t20_world_cup_standings.csv").to_csv(OUT / "t20_wc_standings.csv", index=False)
    load("champions_trophy_standings.csv").to_csv(OUT / "champions_trophy_standings.csv", index=False)

    o = pd.read_csv(OUT / "odi_wc_standings.csv")
    for c in STANDINGS_COLS:
        if c not in o.columns:
            o[c] = None
    extra = [c for c in o.columns if c not in STANDINGS_COLS]
    o = o[STANDINGS_COLS + extra]
    o.to_csv(OUT / "odi_wc_standings.csv", index=False)
    print("standings: t20_wc_standings.csv, champions_trophy_standings.csv, "
          "odi_wc_standings.csv (re-shaped to the shared column set)")


# ---------------------------------------------------------------------------
# 4. Player bios enrichment (T20 WC + Champions Trophy squad lists).
# ---------------------------------------------------------------------------
def attach_bios(players_file, bios_path):
    players = pd.read_csv(OUT / players_file)
    # Idempotent: if this script has already been run once, players_file already has
    # these columns merged in - drop them first so re-running doesn't collide/suffix.
    players = players.drop(columns=[c for c in ["dob", "nationality", "batting_style", "bowling_style"]
                                     if c in players.columns])
    bios = pd.read_csv(bios_path)
    bios = bios[bios.Matched == True][
        ["Team", "Player_Name", "DOB", "Nationality", "Right_Handed_Bat", "Bowling_Style"]]
    # The source also carries batting handedness (Right_Handed_Bat: True/False) - previously
    # dropped here, which is why t20_wc_players.csv/champions_trophy_players.csv had a
    # bowling_style column but no batting_style column at all (unlike odi_wc_players.csv,
    # which has both). Converted to the same "Right-handed"/"Left-handed" wording used there.
    bios["batting_style"] = bios["Right_Handed_Bat"].map({True: "Right-handed", False: "Left-handed"})
    bios = bios.drop(columns=["Right_Handed_Bat"])
    bios = bios.rename(columns={"Team": "team", "Player_Name": "player_name", "DOB": "dob",
                                 "Nationality": "nationality", "Bowling_Style": "bowling_style"})
    bios = bios.drop_duplicates(subset=["team", "player_name"])
    merged = players.merge(bios, on=["team", "player_name"], how="left")
    # Match odi_wc_players.csv's column order: dob, batting_style, bowling_style, ...
    cols = [c for c in merged.columns if c not in ("batting_style", "bowling_style")]
    dob_i = cols.index("dob") + 1
    cols = cols[:dob_i] + ["batting_style", "bowling_style"] + cols[dob_i:]
    merged = merged[cols]
    merged.to_csv(OUT / players_file, index=False)
    matched = merged["dob"].notna().sum()
    print(f"{players_file}: {len(merged)} rows, {matched} with a bio match")


def build_player_bios():
    attach_bios("t20_wc_players.csv", RAW / "player_bios_v2_final" / "t20wc_players_bios.csv")
    attach_bios("champions_trophy_players.csv", RAW / "player_bios_v1" / "ct_players_bios.csv")


# ---------------------------------------------------------------------------
# 5. WTC-only trivia tables.
# ---------------------------------------------------------------------------
def build_wtc_extras():
    pd.read_csv(RAW / "wtc_extras" / "wtc_finals_officials.csv").to_csv(OUT / "wtc_finals_officials.csv", index=False)
    pd.read_csv(RAW / "wtc_extras" / "wtc_highest_partnerships_highlights.csv").to_csv(OUT / "wtc_notable_partnerships.csv", index=False)
    pd.read_csv(RAW / "wtc_extras" / "wtc_officials_illingworth_full.csv").to_csv(OUT / "wtc_umpire_appearances.csv", index=False)
    print("wtc extras: wtc_finals_officials.csv, wtc_notable_partnerships.csv, wtc_umpire_appearances.csv")


# ---------------------------------------------------------------------------
# 6. Team/venue master + name-lookup tables (loaded for reference / light enrichment).
# ---------------------------------------------------------------------------
def build_master_tables():
    pd.read_csv(RAW / "team_venue_master" / "team_master.csv").to_csv(OUT / "team_master.csv", index=False)
    pd.read_csv(RAW / "team_venue_master" / "venue_master.csv").to_csv(OUT / "venue_master.csv", index=False)
    pd.read_csv(RAW / "team_venue_master" / "venue_name_mapping.csv").to_csv(OUT / "venue_name_mapping.csv", index=False)
    with open(RAW / "team_venue_master" / "team_name_lookup.json") as f:
        lookup = json.load(f)
    with open(OUT / "team_name_lookup.json", "w") as f:
        json.dump(lookup, f, indent=2)
    print("master tables: team_master.csv, venue_master.csv, venue_name_mapping.csv, team_name_lookup.json")


def build_wtc_players():
    """
    WTC squad list — this only exists for the 2019-2021 cycle. The original raw-data
    provider's own READMEs for the 2021-2023 and 2023-2025 cycles explicitly say a
    player list wasn't included because reproducing a ~200-player Statsguru export by
    hand (rather than scraping stats.espncricinfo.com) isn't reliable - it's a genuine
    absence in the source, not something skipped here. This is a real, if partial,
    player list (207 players), not "no data" - it was just never wired up before.
    """
    src = Path(__file__).resolve().parents[1] / "data" / "raw" / "archive__13_" / "(1) Players.csv"
    p = pd.read_csv(src)
    out = pd.DataFrame({
        "team": p["Country"],
        "year": 2021,  # aligns with tournament_editions.csv's WTC 2019-2021 row (year=2021)
        "cycle": "2019-2021",
        "player_name": p["Player_Name"],
    })
    out.to_csv(OUT / "wtc_players.csv", index=False)
    print(f"wtc_players.csv: {len(out)} rows (2019-2021 cycle only - see docstring)")


if __name__ == "__main__":
    build_odi_players()
    build_records()
    build_standings()
    build_player_bios()
    build_wtc_extras()
    build_master_tables()
    build_wtc_players()
    print("Gap-fill load complete.")
