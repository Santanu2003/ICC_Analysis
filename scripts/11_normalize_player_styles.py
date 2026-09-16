"""Normalize batting_style / bowling_style display values across the three squad datasets.

Why this exists
---------------
The three squad CSVs were assembled from different sources and ended up with the same
meaning written several different ways, which looked broken once the Squads UI started
rendering both columns side by side:

  batting_style  odi_wc : "Right hand" / "Right-hand" / "Right-handed"  (3 spellings)
                 t20/ct : "Right-handed"                                (already clean)

  bowling_style  odi_wc : "Left arm fast-medium" / "Left-arm fast-medium" (spacing drift)
                 t20/ct : "OFF_SPIN" / "MEDIUM_SEAM" raw enums MIXED with
                          "Right-arm off break" human strings in the same column

This rewrites them to one consistent display vocabulary. It only ever rewrites the
*wording* of a value - it never invents a style for a player who had none (blanks stay
blank; see docs/DATA_SOURCES.md "Known gaps"), and it never changes which hand/type a
player bowls.

Idempotent: safe to re-run, second run is a no-op.
"""
import re
from pathlib import Path

import pandas as pd

PROCESSED = Path(__file__).resolve().parents[1] / "data" / "processed"
FILES = ["odi_wc_players.csv", "t20_wc_players.csv", "champions_trophy_players.csv"]

# Raw enums used by the player-bios source (t20_wc / champions_trophy only). These carry
# no handedness, so they stay handedness-free rather than guessing "Right-arm".
ENUM_BOWLING = {
    "FAST_SEAM": "Fast seam",
    "MEDIUM_SEAM": "Medium seam",
    "OFF_SPIN": "Off spin",
    "LEG_SPIN": "Leg spin",
    "ORTHODOX": "Orthodox spin",
    "UNORTHODOX": "Unorthodox spin",
}


def norm_batting(v):
    if not isinstance(v, str) or not v.strip():
        return v
    s = v.strip()
    low = s.lower()
    if low.startswith("right"):
        return "Right-handed"
    if low.startswith("left"):
        return "Left-handed"
    return s


def norm_bowling(v):
    if not isinstance(v, str) or not v.strip():
        return v
    s = v.strip()
    if s.upper() in ENUM_BOWLING:
        return ENUM_BOWLING[s.upper()]
    # "Left arm fast-medium" -> "Left-arm fast-medium"; also collapses double spaces.
    s = re.sub(r"^(left|right)\s+arm", lambda m: m.group(1).capitalize() + "-arm", s, flags=re.I)
    s = re.sub(r"^(left|right)-arm", lambda m: m.group(1).capitalize() + "-arm", s, flags=re.I)
    s = re.sub(r"\s+", " ", s)
    # Unify the fast-medium / medium-fast family on hyphens.
    s = re.sub(r"\bfast medium\b", "fast-medium", s, flags=re.I)
    s = re.sub(r"\bmedium fast\b", "medium-fast", s, flags=re.I)
    return s[0].upper() + s[1:] if s else s


def main():
    for fname in FILES:
        path = PROCESSED / fname
        if not path.exists():
            print(f"  skip (missing): {fname}")
            continue
        d = pd.read_csv(path)
        before_bat = d["batting_style"].dropna().nunique() if "batting_style" in d.columns else 0
        before_bowl = d["bowling_style"].dropna().nunique() if "bowling_style" in d.columns else 0

        if "batting_style" in d.columns:
            d["batting_style"] = d["batting_style"].map(norm_batting)
        if "bowling_style" in d.columns:
            d["bowling_style"] = d["bowling_style"].map(norm_bowling)

        after_bat = d["batting_style"].dropna().nunique() if "batting_style" in d.columns else 0
        after_bowl = d["bowling_style"].dropna().nunique() if "bowling_style" in d.columns else 0
        d.to_csv(path, index=False)
        print(f"  {fname:34s} batting {before_bat:2d} -> {after_bat:2d} variants | "
              f"bowling {before_bowl:2d} -> {after_bowl:2d} variants")


if __name__ == "__main__":
    print("Normalizing player style values...")
    main()
    print("Done.")
