"""
GAP-FILL DETAILED STATS LOAD — Sept 2026 (2nd batch).

Adds ESPNcricinfo Statsguru-style records (most runs/wickets career, best bowling
figures innings/match, career/innings economy rates, most runs conceded in an innings,
most five-/ten-wicket hauls, most wickets in a series) for all 4 formats.

This sits ALONGSIDE {fmt}_records.csv (added in the previous gap-fill pass) rather than
replacing it: that file is a curated "notable records" summary (Category/Rank/
Player_team/Detail/Value); this one is the fuller Statsguru-style data with real
per-stat columns (Mat/Inns/Ave/SR/BBI/Econ/etc), for a proper stats browser.

Output: one {fmt}_detailed_stats.csv per format. Every row is tagged with a 'stat' key
from a shared taxonomy so the same category lines up across formats:
  most_runs, most_wickets, best_bowling_innings, best_economy_career,
  best_economy_innings, most_runs_conceded, most_five_wicket_hauls  -> all 4 formats
  most_wickets_series                                                -> odi_wc/t20_wc/champions_trophy only
  best_bowling_match, most_ten_wicket_hauls                          -> wtc only (only meaningful
                                                                         in a 2-innings Test match)

Column names are normalised across sources first, since the 4 source folders don't spell
the same stat the same way (e.g. ODI WC/T20 WC use bare "4"/"5"/"10" for wicket-haul
thresholds, Champions Trophy/WTC use "4w"/"5w"/"10w"; "MatchDate" vs "Match Date";
"ODI#"/"Test#"/"Scorecard" vs a shared "Match ID"; "Edition" vs "Series").
"""
import pandas as pd
from pathlib import Path

RAW = Path(__file__).resolve().parents[1] / "data" / "raw" / "gap_fill_2026-09-13"
OUT = Path(__file__).resolve().parents[1] / "data" / "processed"

RENAME = {
    "0": "Ducks", "100": "100s", "50": "50s",
    "4": "4w", "5": "5w", "10": "10w",
    "MatchDate": "Match Date",
    "ODI#": "Match ID", "Scorecard": "Match ID", "Test#": "Match ID", "T20I#": "Match ID",
    "Edition": "Series",
}

SOURCES = {
    "odi_wc": ("odi_wc_records_detailed", {
        "most_runs_career.csv": "most_runs",
        "most_wickets_career.csv": "most_wickets",
        "best_bowling_figures_innings.csv": "best_bowling_innings",
        "best_economy_rates_career.csv": "best_economy_career",
        "best_economy_rates_innings.csv": "best_economy_innings",
        "most_runs_conceded_innings.csv": "most_runs_conceded",
        "most_five_wicket_hauls.csv": "most_five_wicket_hauls",
        "most_wickets_series.csv": "most_wickets_series",
    }),
    "t20_wc": ("t20_wc_records_detailed", {
        "most_runs_career.csv": "most_runs",
        "most_wickets_career.csv": "most_wickets",
        "best_bowling_figures_innings.csv": "best_bowling_innings",
        "best_economy_rates_career.csv": "best_economy_career",
        "best_economy_rates_innings.csv": "best_economy_innings",
        "most_runs_conceded_innings.csv": "most_runs_conceded",
        "most_five_wicket_hauls.csv": "most_five_wicket_hauls",
        "most_wickets_series.csv": "most_wickets_series",
    }),
    "champions_trophy": ("champions_trophy_records_detailed", {
        "most_runs.csv": "most_runs",
        "most_wickets.csv": "most_wickets",
        "best_bowling_innings.csv": "best_bowling_innings",
        "best_economy_rate_career.csv": "best_economy_career",
        "best_economy_rate_innings.csv": "best_economy_innings",
        "most_runs_conceded_innings.csv": "most_runs_conceded",
        "most_5wi_career.csv": "most_five_wicket_hauls",
        "most_wickets_series.csv": "most_wickets_series",
    }),
    "wtc": ("wtc_records_detailed", {
        "most_runs.csv": "most_runs",
        "most_wickets.csv": "most_wickets",
        "best_bowling_innings.csv": "best_bowling_innings",
        "best_bowling_match.csv": "best_bowling_match",
        "best_economy_rate_career.csv": "best_economy_career",
        "best_economy_rate_innings.csv": "best_economy_innings",
        "most_runs_conceded_innings.csv": "most_runs_conceded",
        "most_5wi_career.csv": "most_five_wicket_hauls",
        "most_10wm_career.csv": "most_ten_wicket_hauls",
    }),
}

STAT_LABELS = {
    "most_runs": "Most Runs (career)",
    "most_wickets": "Most Wickets (career)",
    "best_bowling_innings": "Best Bowling Figures (innings)",
    "best_bowling_match": "Best Bowling Figures (match)",
    "best_economy_career": "Best Economy Rate (career)",
    "best_economy_innings": "Best Economy Rate (innings)",
    "most_runs_conceded": "Most Runs Conceded (innings)",
    "most_five_wicket_hauls": "Most Five-Wicket Hauls (career)",
    "most_ten_wicket_hauls": "Most Ten-Wicket Hauls (career)",
    "most_wickets_series": "Most Wickets (single series/edition)",
}

if __name__ == "__main__":
    for fmt, (folder, files) in SOURCES.items():
        frames = []
        for fname, stat_key in files.items():
            p = RAW / folder / fname
            d = pd.read_csv(p)
            # Source files are already rank-ordered but ship inconsistent lengths per
            # category (anywhere from ~10 to ~45 rows). Cap every category at its top 20
            # so the UI is consistent everywhere; categories with fewer than 20 rows on
            # record (e.g. rarer feats like most ten-wicket hauls) just keep everything
            # they have rather than being padded out.
            d = d.head(20)
            d = d.rename(columns={k: v for k, v in RENAME.items() if k in d.columns})
            d.insert(0, "stat", stat_key)
            d.insert(1, "stat_label", STAT_LABELS[stat_key])
            d.insert(2, "rank", range(1, len(d) + 1))
            frames.append(d)
        out = pd.concat(frames, ignore_index=True, sort=False)
        out.to_csv(OUT / f"{fmt}_detailed_stats.csv", index=False)
        print(f"{fmt}_detailed_stats.csv: {len(out)} rows across {len(files)} categories")
    print("Detailed stats load complete.")
