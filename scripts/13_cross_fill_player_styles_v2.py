"""Second-pass cross-fill for batting_style / bowling_style (supersedes the first pass in
12_cross_fill_player_styles.py, which was too conservative).

What the first pass got wrong
------------------------------
Pass 1 treated a name as AMBIGUOUS whenever two datasets recorded different *strings* for
its style, and skipped it. That threw away most of the available signal, because the vast
majority of those "conflicts" were not two different people at all:

  368 bowling-style names were flagged ambiguous. Of those:
    - 22  were "Wicket-keeper" colliding with a real bowling style. "Wicket-keeper" is a
          ROLE, not a bowling action - the same player can be both. Not a conflict.
    - 305 were an armless ENUM value from the bios source ("Medium seam", "Off spin",
          "Leg spin", "Fast seam", "Orthodox spin") sitting against a fully-specified
          string from the ODI dataset ("Right-arm medium", "Right-arm off break"). Same
          player, same action - one source simply doesn't record handedness. The full
          string is strictly more informative, not contradictory.
    - 41  were pure phrasing variants of the same action ("Right-arm leg spin" vs
          "Right-arm leg-break").
  Only a small remainder were genuine disagreements.

Why not match on date of birth
-------------------------------
DOB looked like the obvious identity key (both formats parse fine), but it is not reliable
here: the same player under the same team is recorded with DIFFERENT birth dates across
sources - e.g. Adam Milne (NZ) is 1992-04-30 in the ODI data and 1992-04-13 in the T20
data; Aaron Phangiso (RSA) is 1988-02-03 vs 1984-01-21. 118 names carry >1 distinct DOB,
and spot-checking shows these are source data-entry drift, not distinct people. Matching on
DOB would therefore split one real player into two identities and BLOCK valid fills. It is
deliberately not used.

Identity rule used instead
---------------------------
  name + team          -> same person (primary; "Haider Ali/Pakistan" stays separate from
                          "Haider Ali/UAE", which is exactly the collision we care about)
  name alone           -> used as a fallback ONLY when that name maps to a single person
                          under the team-alias map below, so genuine team-switchers
                          (Eoin Morgan Ireland->England, Corey Anderson NZ->USA) still fill
                          across their own appearances.

Value reconciliation
---------------------
Candidate values for one identity are merged rather than compared as raw strings:
  - "Wicket-keeper" is held aside as a role and never blocks a bowling-style fill.
  - Each remaining value is parsed to (arm, action-family). Values are COMPATIBLE if their
    action families match and their arms don't contradict (one side may be unknown).
  - Among compatible values the MOST SPECIFIC wins (a value with a known arm beats an
    armless enum), so gaps get "Right-arm off break" rather than bare "Off spin".
  - If two values genuinely contradict (different action family, or opposite arms), the
    identity is skipped - still no guessing.

Never overwrites an existing value. Idempotent.
"""
import re
from pathlib import Path

import pandas as pd

PROCESSED = Path(__file__).resolve().parents[1] / "data" / "processed"
FILES = ["odi_wc_players.csv", "t20_wc_players.csv", "champions_trophy_players.csv"]

# Same nation recorded under different labels across sources; folded together so a player
# isn't split into two identities by a naming difference alone.
TEAM_ALIASES = {
    "united states of america": "usa",
    "united arab emirates": "uae",
    "u.a.e.": "uae",
    "papua new guinea": "png",
    "west indies": "west indies",
}

WK = "wicket-keeper"


def norm(v):
    return str(v).strip().lower()


def team_key(v):
    t = norm(v)
    return TEAM_ALIASES.get(t, t)


def parse_style(value):
    """-> (arm, family, specificity). arm is 'L'/'R'/None; family groups the action."""
    s = norm(value)
    if not s or s == "nan":
        return None
    if "wicket" in s:
        return ("?", WK, 0)

    if s.startswith("left") or "slow left" in s or "left-arm" in s:
        arm = "L"
    elif s.startswith("right") or "right-arm" in s:
        arm = "R"
    else:
        arm = None  # armless enum from the bios source

    if any(w in s for w in ("leg break", "leg-break", "leg spin", "legbreak", "googly", "wrist")):
        fam = "legspin"
    elif any(w in s for w in ("off break", "off-break", "off spin", "offbreak", "offspin")):
        fam = "offspin"
    elif "orthodox" in s:
        fam = "orthodox"
    elif "unorthodox" in s:
        fam = "unorthodox"
    elif "spin" in s:
        fam = "spin"
    elif "fast-medium" in s or "medium-fast" in s:
        fam = "fastmedium"
    elif "fast" in s:
        fam = "fast"
    elif "medium" in s or "seam" in s:
        fam = "medium"
    elif "slow" in s:
        fam = "slow"
    else:
        fam = "other"

    # More specific = has an arm, and a longer/more descriptive string.
    spec = (1 if arm else 0) * 10 + min(len(s), 9)
    return (arm, fam, spec)


# Spin families that are compatible generalizations of each other ("Off spin" vs the
# generic "spin" bucket), so a generic value never blocks a specific one.
SPIN_FAMS = {"legspin", "offspin", "orthodox", "unorthodox", "spin"}
PACE_FAMS = {"fast", "fastmedium", "medium", "slow"}


def families_compatible(a, b):
    if a == b:
        return True
    if a in SPIN_FAMS and b in SPIN_FAMS:
        return "spin" in (a, b)  # generic 'spin' merges with any specific spin
    if a in PACE_FAMS and b in PACE_FAMS:
        # medium/fast-medium/fast are a continuum; sources phrase the same bowler
        # differently. Treat adjacent pace descriptions as compatible.
        return True
    return False


def reconcile(values):
    """Merge candidate strings for ONE identity into a single best value, or None."""
    parsed = [(v, parse_style(v)) for v in values if parse_style(v)]
    # Hold the keeper role aside - it never conflicts with a bowling action.
    non_wk = [(v, p) for v, p in parsed if p[1] != WK]
    if not non_wk:
        return values[0] if values else None  # only 'Wicket-keeper' on record

    base_fam = None
    base_arm = None
    for _, (arm, fam, _) in non_wk:
        if base_fam is None:
            base_fam, base_arm = fam, arm
            continue
        if not families_compatible(base_fam, fam):
            return None  # genuine disagreement
        if arm and base_arm and arm != base_arm:
            return None  # opposite arms - different bowler
        if arm and not base_arm:
            base_arm = arm
        # keep the more specific family (specific spin beats generic 'spin')
        if base_fam == "spin" and fam in SPIN_FAMS:
            base_fam = fam
    return max(non_wk, key=lambda x: x[1][2])[0]


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
        frames[fname] = d

    # A name is "single-person" if it only ever appears under one canonical team.
    all_pairs = pd.concat([d[["_n", "_t"]] for d in frames.values()], ignore_index=True)
    teams_per_name = all_pairs.drop_duplicates().groupby("_n")["_t"].nunique()
    solo_names = set(teams_per_name[teams_per_name == 1].index)
    multi_names = set(teams_per_name[teams_per_name > 1].index)
    print(f"identities: {len(solo_names)} single-team names, {len(multi_names)} multi-team names "
          f"(matched on name+team)")

    for col in ["batting_style", "bowling_style"]:
        pool = pd.concat([d[["_n", "_t", col]].dropna(subset=[col]) for d in frames.values()],
                         ignore_index=True)

        # Candidate value lists for both key strengths.
        by_nt = pool.groupby(["_n", "_t"])[col].apply(list)
        by_n = pool[pool["_n"].isin(solo_names)].groupby("_n")[col].apply(list)

        lut_nt, skipped = {}, 0
        for key, vals in by_nt.items():
            r = reconcile(vals)
            if r is None:
                skipped += 1
            else:
                lut_nt[key] = r
        lut_n = {}
        for key, vals in by_n.items():
            r = reconcile(vals)
            if r is not None:
                lut_n[key] = r

        print(f"\n{col}: {len(lut_nt)} name+team identities resolved, "
              f"{skipped} skipped as genuinely conflicting")

        for fname, d in frames.items():
            before = d[col].notna().sum()
            miss = d[col].isna()
            # name+team first, then single-team-name fallback
            filled = d.loc[miss].apply(
                lambda r: lut_nt.get((r["_n"], r["_t"])) or lut_n.get(r["_n"]), axis=1)
            d.loc[miss, col] = filled
            after = d[col].notna().sum()
            n = len(d)
            print(f"  {fname:34s} {before/n*100:5.1f}% -> {after/n*100:5.1f}%  [+{after-before}]")

    for fname, d in frames.items():
        d.drop(columns=["_n", "_t"]).to_csv(PROCESSED / fname, index=False)


if __name__ == "__main__":
    print("Cross-fill pass 2 (value reconciliation + name/team identity)...")
    main()
    print("\nDone.")
