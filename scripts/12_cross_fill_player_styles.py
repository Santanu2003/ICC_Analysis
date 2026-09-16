"""Fill missing batting_style / bowling_style by cross-referencing the SAME real player's
other tournament appearances, instead of leaving every gap blank.

Why this exists
----------------
T20 WC and Champions Trophy's player-bios source only covers 77-97% of players per edition
for batting style and 51-54% for bowling style (worse for the newest editions: T20 WC 2026
~52%, Champions Trophy 2025 ~59% - see docs/DATA_SOURCES.md). But a lot of these players
ALSO appear in the ODI World Cup dataset (100% batting/95% bowling coverage) or in the
*other* T20 WC/Champions Trophy dataset, under a bio that DOES have the style recorded -
same human being, same batting hand, same bowling arm. This fills those specific gaps from
that player's own other appearance rather than leaving a blank the data supports.

Safety rule (why some names still don't get filled)
-----------------------------------------------------
Matching is done on normalized player name only (no DOB/team key available across all three
sources consistently), so a handful of names could in principle belong to two different real
people (common names recur, e.g. two different "Haider Ali"s). To avoid mis-attributing one
player's style to a different player who shares their name:
  - For a given name, every NON-NULL value already on record for that style, across all
    three datasets, must agree exactly.
  - If two different values show up under the same name (e.g. AB de Villiers is logged as
    both "Wicket-keeper" and "Medium seam" for bowling, because one dataset recorded his
    keeping role and another recorded his bowling arm), that name is treated as AMBIGUOUS
    and is skipped entirely - no fill, no guess. Better to leave a real gap than risk a
    wrong badge on a player card.
  - A name switching TEAMS across appearances (e.g. Eoin Morgan: Ireland -> England) is
    fine and still fills, since batting hand/bowling arm are intrinsic to the player, not
    the team - team is not part of the agreement check.

This never touches a cell that already has a value - only fills where a dataset's own
column is blank. Idempotent: safe to re-run.
"""
from pathlib import Path

import pandas as pd

PROCESSED = Path(__file__).resolve().parents[1] / "data" / "processed"
FILES = ["odi_wc_players.csv", "t20_wc_players.csv", "champions_trophy_players.csv"]
STYLE_COLS = ["batting_style", "bowling_style"]


def norm(name):
    return str(name).strip().lower()


def build_safe_lookup(frames, col):
    """One Series per style column: normalized name -> the single value every dataset
    agrees on. Names with conflicting recorded values are dropped (see module docstring)."""
    parts = [f[["_key", col]].dropna(subset=[col]) for f in frames if col in f.columns]
    if not parts:
        return pd.Series(dtype=object), set()
    allrows = pd.concat(parts, ignore_index=True)
    n_distinct = allrows.groupby("_key")[col].nunique()
    ambiguous = set(n_distinct[n_distinct > 1].index)
    safe = allrows[~allrows["_key"].isin(ambiguous)].drop_duplicates("_key").set_index("_key")[col]
    return safe, ambiguous


def main():
    frames = {}
    for fname in FILES:
        path = PROCESSED / fname
        if not path.exists():
            print(f"  skip (missing): {fname}")
            continue
        d = pd.read_csv(path)
        d["_key"] = d["player_name"].map(norm)
        frames[fname] = d

    for col in STYLE_COLS:
        safe, ambiguous = build_safe_lookup(frames.values(), col)
        print(f"\n{col}: {len(safe)} unambiguous names available to fill from, "
              f"{len(ambiguous)} names excluded as ambiguous")

        for fname, d in frames.items():
            if col not in d.columns:
                continue
            before = d[col].notna().sum()
            missing = d[col].isna()
            fill_values = d.loc[missing, "_key"].map(safe)
            d.loc[missing, col] = fill_values
            after = d[col].notna().sum()
            n = len(d)
            print(f"  {fname:34s} {before:5d}/{n} ({before/n*100:5.1f}%) -> "
                  f"{after:5d}/{n} ({after/n*100:5.1f}%)  [+{after-before} filled]")

    for fname, d in frames.items():
        d.drop(columns=["_key"]).to_csv(PROCESSED / fname, index=False)


if __name__ == "__main__":
    print("Cross-filling batting/bowling style from other tournament appearances...")
    main()
    print("\nDone. Re-run docs/DATA_SOURCES.md coverage numbers if you track them there.")
