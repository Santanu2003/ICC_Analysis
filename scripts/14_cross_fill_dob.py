"""Cross-fill missing `dob` the same way scripts/13 fills batting/bowling style: same
player, same identity (name+team), different dataset already has it recorded.

Why DOB wasn't in the original cross-fill pass
-------------------------------------------------
Script 13's docstring flagged DOB as unreliable for use as the MATCHING key, because the
same real player has different birth dates recorded across sources (Adam Milne NZ:
1992-04-30 in the ODI data vs 1992-04-13 in the T20 data). That's still true and DOB is
still not used to decide "is this the same person" here either - identity is name+team,
exactly as in script 13.

But that's a different question from "should a missing dob cell be filled from another
dataset's value for the same identity" - and the answer is yes, PROVIDED the same
conflict-detection applies: if an identity's known dob values (across all 3 datasets)
disagree, that identity is flagged conflicting and left alone rather than guessing which
one is right. Only identities with a single, consistent recorded dob get used to fill
gaps. 118 identities are expected to hit this conflict flag (same count found by script
13) and stay unfilled - a real data-quality issue in the source, not something to paper
over here.

Output format
-------------
The three datasets use different date conventions (ODI: "15 July 1950", T20/Champions
Trophy: "1992-04-30" ISO). A filled cell is written in whichever convention that TARGET
column already uses, so no column ends up with two different date formats mixed together.
Existing non-null cells are never touched or reformatted.

Idempotent: safe to re-run.
"""
from pathlib import Path

import pandas as pd

PROCESSED = Path(__file__).resolve().parents[1] / "data" / "processed"
FILES = ["odi_wc_players.csv", "t20_wc_players.csv", "champions_trophy_players.csv"]

TEAM_ALIASES = {
    "united states of america": "usa",
    "united arab emirates": "uae",
    "u.a.e.": "uae",
    "papua new guinea": "png",
}

# Per-file, the date convention to WRITE filled values in - matches what that file's own
# non-null dob cells already look like, so nothing looks mixed. ODI's "%-d"-style
# no-leading-zero day isn't a portable strftime flag (Linux-only, breaks on Windows), so
# that one is built manually in `fmt_out` below instead of via strftime.
OUT_FORMAT = {
    "odi_wc_players.csv": "odi",             # -> "15 July 1950"
    "t20_wc_players.csv": "%Y-%m-%d",        # "1992-04-30"
    "champions_trophy_players.csv": "%Y-%m-%d",
}


def fmt_out(ts, fmt):
    if fmt == "odi":
        return f"{ts.day} {ts.strftime('%B %Y')}"
    return ts.strftime(fmt)


def norm(v):
    return str(v).strip().lower()


def team_key(v):
    t = norm(v)
    return TEAM_ALIASES.get(t, t)


def parse_dob(v):
    if pd.isna(v):
        return None
    s = str(v).strip()
    for fmt in ("%Y-%m-%d", "%d %B %Y", "%d %b %Y"):
        try:
            return pd.to_datetime(s, format=fmt)
        except ValueError:
            continue
    try:
        return pd.to_datetime(s)
    except (ValueError, TypeError):
        return None


def main():
    frames = {}
    for fname in FILES:
        p = PROCESSED / fname
        if not p.exists():
            print(f"  skip (missing): {fname}")
            continue
        d = pd.read_csv(p)
        d["_n"] = d["player_name"].map(norm)
        d["_t"] = d["team"].map(team_key)
        d["_parsed_existing_dob"] = d["dob"].map(parse_dob)
        frames[fname] = d

    pool = pd.concat(
        [d[["_n", "_t", "_parsed_existing_dob"]].dropna(subset=["_parsed_existing_dob"])
         for d in frames.values()],
        ignore_index=True,
    )
    # One identity's set of distinct known dates (as ISO strings, for exact comparison).
    pool["_iso"] = pool["_parsed_existing_dob"].dt.strftime("%Y-%m-%d")
    by_identity = pool.groupby(["_n", "_t"])["_iso"].agg(lambda s: sorted(set(s)))

    lut = {}
    conflicts = 0
    for key, vals in by_identity.items():
        if len(vals) == 1:
            lut[key] = pd.to_datetime(vals[0])
        else:
            conflicts += 1

    print(f"dob: {len(lut)} name+team identities with a single consistent dob available, "
          f"{conflicts} skipped as conflicting (multiple different dates on record)")

    for fname, d in frames.items():
        before = d["dob"].notna().sum()
        miss = d["dob"].isna()
        resolved = d.loc[miss].apply(lambda r: lut.get((r["_n"], r["_t"])), axis=1)
        out_fmt = OUT_FORMAT[fname]
        formatted = resolved.map(lambda x: fmt_out(x, out_fmt) if pd.notna(x) else None)
        d.loc[miss, "dob"] = formatted
        after = d["dob"].notna().sum()
        n = len(d)
        print(f"  {fname:34s} {before/n*100:5.1f}% -> {after/n*100:5.1f}%  [+{after-before}]")

    for fname, d in frames.items():
        d.drop(columns=["_n", "_t", "_parsed_existing_dob"]).to_csv(PROCESSED / fname, index=False)


if __name__ == "__main__":
    print("Cross-filling missing dob from other tournament appearances...")
    main()
    print("\nDone.")
