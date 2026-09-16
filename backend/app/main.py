from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import os
import re
import pandas as pd

app = FastAPI(title="ICC Tournaments Analytics API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False, allow_methods=["*"], allow_headers=["*"])

# Same dual-layout resolution as the FIFA API this project pairs with: native/Render runs
# have main.py at <repo>/backend/app/main.py with data two levels up, the Docker image
# copies it to /app/app/main.py with data one level up.
_here = Path(__file__).resolve()
_candidates = [
    Path(os.environ["ICC_DATA_DIR"]) if os.environ.get("ICC_DATA_DIR") else None,
    _here.parents[2] / "data" / "processed",
    _here.parents[1] / "data" / "processed",
]
DATA = next((c.resolve() for c in _candidates if c and c.exists()), _candidates[1].resolve())

FORMATS = {
    "odi_wc": {"label": "ODI World Cup", "matches": "odi_wc_matches.csv"},
    "t20_wc": {"label": "T20 World Cup", "matches": "t20_wc_matches.csv"},
    "champions_trophy": {"label": "Champions Trophy", "matches": "champions_trophy_matches.csv"},
    "wtc": {"label": "World Test Championship", "matches": "wtc_matches.csv"},
}


def read(name):
    p = DATA / name
    if not p.exists():
        raise HTTPException(500, f"Dataset not found: {name}")
    return pd.read_csv(p)


def clean_records(df):
    return df.astype(object).where(pd.notna(df), None).to_dict("records")


def norm(s):
    return str(s).strip().casefold()


def check_format(fmt):
    if fmt not in FORMATS:
        raise HTTPException(404, f"Unknown format '{fmt}'. Use one of: {', '.join(FORMATS)}")


# Every format's matches table has a 'winner', 'team1'/'team2' (or 'Team 1'/'Team 2') pair
# so team-level aggregate stats (matches, wins, losses) can be computed uniformly across
# all 4 tournaments from raw match rows, without needing a bespoke per-format stats file.
def team_stats_from_matches(m):
    long = pd.concat([
        m[["team1", "winner"]].rename(columns={"team1": "team"}),
        m[["team2", "winner"]].rename(columns={"team2": "team"}),
    ], ignore_index=True)
    long = long.dropna(subset=["team"])
    rows = []
    for team, grp in long.groupby("team"):
        played = len(grp)
        winner_norm = grp.winner.map(lambda w: norm(w) if pd.notna(w) else None)
        wins = int((winner_norm == norm(team)).sum())
        no_result = int(winner_norm.isna().sum() + winner_norm.isin(["-", "drawn", "tied", "tie", "no result"]).sum())
        losses = max(played - wins - no_result, 0)
        rows.append({"team": team, "matches": played, "wins": wins, "losses": losses, "no_result_or_draw": no_result})
    df = pd.DataFrame(rows).sort_values(["wins", "matches"], ascending=False)
    return enrich_with_team_master(df)


# Loaded once at startup (Sept 2026 gap-fill data) - full_name/abbreviation/region tags
# merged onto team stats wherever a name match is found. A missing file or a team that
# doesn't match anything in it is a no-op, not an error, since this is enrichment only.
try:
    _TEAM_MASTER = pd.read_csv(DATA / "team_master.csv")
except FileNotFoundError:
    _TEAM_MASTER = pd.DataFrame(columns=["full_name", "abbreviation", "region", "is_test_nation"])


# A handful of team-master lookups need an alias since the full_name spelling there
# doesn't match every raw source's spelling (e.g. WTC/CT data already say "U.A.E." but
# ODI WC/T20 WC data say "United Arab Emirates" or just "UAE").
_TEAM_ALIASES = {"united arab emirates": "u.a.e.", "uae": "u.a.e."}


def _team_key(name):
    n = norm(name)
    return _TEAM_ALIASES.get(n, n)


def enrich_with_team_master(df):
    if _TEAM_MASTER.empty or df.empty:
        return df
    tm = _TEAM_MASTER[["full_name", "abbreviation", "region"]].copy()
    tm["_key"] = tm.full_name.map(_team_key)
    df = df.copy()
    df["_key"] = df.team.map(_team_key)
    df = df.merge(tm.drop(columns=["full_name"]), on="_key", how="left").drop(columns=["_key"])
    return df


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "icc-tournaments-api", "version": "1.0.0"}


@app.get("/api/formats")
def formats():
    return [{"key": k, "label": v["label"]} for k, v in FORMATS.items()]


@app.get("/api/editions")
def editions(tournament: str | None = None):
    d = read("tournament_editions.csv")
    if tournament:
        d = d[d.tournament.map(norm).str.contains(norm(tournament), na=False)]
    return clean_records(d.sort_values(["tournament", "year"]))


@app.get("/api/editions/{tournament}/{year}")
def edition(tournament: str, year: int):
    d = read("tournament_editions.csv")
    r = d[d.tournament.map(norm).eq(norm(tournament)) & d.year.eq(year)]
    if r.empty:
        raise HTTPException(404, "Edition not found")
    return clean_records(r)[0]


@app.get("/api/{fmt}/matches")
def matches(fmt: str, year: int | None = None, cycle: str | None = None, team: str | None = None, limit: int = Query(1000, ge=1, le=2000)):
    check_format(fmt)
    d = read(FORMATS[fmt]["matches"])
    if year is not None and "year" in d.columns:
        d = d[d.year.eq(year)]
    if cycle is not None and "cycle" in d.columns:
        d = d[d.cycle.eq(cycle)]
    if team:
        d = d[d.team1.map(norm).str.contains(norm(team), na=False) | d.team2.map(norm).str.contains(norm(team), na=False)]
    date_col = "match_date"
    sort_cols = [c for c in [date_col] if c in d.columns]
    if sort_cols:
        d = d.sort_values(sort_cols)
    return clean_records(d.head(limit))


@app.get("/api/{fmt}/matches/{match_id}")
def match_detail(fmt: str, match_id: str):
    check_format(fmt)
    d = read(FORMATS[fmt]["matches"])
    r = d[d.match_id.eq(match_id)]
    if r.empty:
        raise HTTPException(404, "Match not found")
    return clean_records(r)[0]


@app.get("/api/{fmt}/teams")
def teams(fmt: str, limit: int = Query(60, ge=1, le=100)):
    check_format(fmt)
    m = read(FORMATS[fmt]["matches"])
    return clean_records(team_stats_from_matches(m).head(limit))


@app.get("/api/{fmt}/teams/{team}")
def team(fmt: str, team: str):
    check_format(fmt)
    m = read(FORMATS[fmt]["matches"])
    stats = team_stats_from_matches(m)
    r = stats[stats.team.map(norm).eq(norm(team))]
    if r.empty:
        raise HTTPException(404, "Team not found")
    matches_played = m[(m.team1.map(norm).eq(norm(team))) | (m.team2.map(norm).eq(norm(team)))]
    date_col = "match_date"
    if date_col in matches_played.columns:
        matches_played = matches_played.sort_values(date_col)
    return {"stats": clean_records(r)[0], "matches": clean_records(matches_played)}


@app.get("/api/{fmt}/teams/compare/{team_a}/{team_b}")
def compare(fmt: str, team_a: str, team_b: str):
    check_format(fmt)
    m = read(FORMATS[fmt]["matches"])
    na, nb = norm(team_a), norm(team_b)
    h2h = m[(m.team1.map(norm).eq(na) & m.team2.map(norm).eq(nb)) | (m.team1.map(norm).eq(nb) & m.team2.map(norm).eq(na))]
    if h2h.empty:
        raise HTTPException(404, "No head-to-head matches found between these teams")
    date_col = "match_date"
    if date_col in h2h.columns:
        h2h = h2h.sort_values(date_col)
    wins_a = int((h2h.winner.map(norm) == na).sum())
    wins_b = int((h2h.winner.map(norm) == nb).sum())
    other = len(h2h) - wins_a - wins_b
    return {
        "team_a": team_a, "team_b": team_b,
        "head_to_head": {"matches_played": len(h2h), "wins_a": wins_a, "wins_b": wins_b,
                          "draws_or_no_result": other, "matches": clean_records(h2h)},
    }


@app.get("/api/{fmt}/players")
def players(fmt: str, year: int | None = None, team: str | None = None, limit: int = Query(2000, ge=1, le=5000)):
    check_format(fmt)
    fname = {"odi_wc": "odi_wc_players.csv", "t20_wc": "t20_wc_players.csv", "champions_trophy": "champions_trophy_players.csv", "wtc": "wtc_players.csv"}.get(fmt)
    if not fname:
        raise HTTPException(404, f"No player-list dataset for '{fmt}'.")
    d = read(fname)
    if year is not None:
        d = d[d.year.eq(year)]
    if team:
        d = d[d.team.map(norm).str.contains(norm(team), na=False)]
    return clean_records(d.head(limit))


# Records leaderboards - one shared shape (category/rank/player_team/detail/value, plus
# a 'cycle' column for WTC only) across all 4 formats, so this single endpoint replaces
# what used to be a WTC-only route and a T20-only per-category route.
@app.get("/api/{fmt}/records")
def format_records(fmt: str, category: str | None = None, cycle: str | None = None):
    check_format(fmt)
    d = read(f"{fmt}_records.csv")
    if cycle and "cycle" in d.columns:
        d = d[d.cycle.eq(cycle)]
    if category:
        d = d[d.category.map(norm).str.contains(norm(category), na=False)]
    sort_cols = [c for c in ["cycle", "category", "rank"] if c in d.columns]
    return clean_records(d.sort_values(sort_cols) if sort_cols else d)


# Group-stage standings - one shared shape across the 3 edition-based formats. WTC's
# league/cycle scoring (Points+PCT, Won/Lost/Draw/Tied) is a genuinely different shape
# and keeps its own /api/wtc/points-tables endpoint below rather than being forced in here.
@app.get("/api/{fmt}/standings")
def standings(fmt: str, year: int | None = None):
    valid = {"odi_wc", "t20_wc", "champions_trophy"}
    if fmt not in valid:
        raise HTTPException(404, f"No group-stage standings for '{fmt}'. Use one of: {', '.join(valid)}. "
                                  f"World Test Championship uses /api/wtc/points-tables instead.")
    d = read(f"{fmt}_standings.csv")
    if year is not None:
        d = d[d.year.eq(year)]
    sort_cols = [c for c in ["year", "stage", "group", "pos"] if c in d.columns and d[c].notna().any()]
    if "pos" not in sort_cols and "pt" in d.columns:
        d = d.sort_values(sort_cols + ["pt"], ascending=[True] * len(sort_cols) + [False])
    elif sort_cols:
        d = d.sort_values(sort_cols)
    return clean_records(d)


@app.get("/api/{fmt}/detailed-stats")
def detailed_stats(fmt: str, stat: str | None = None):
    check_format(fmt)
    d = read(f"{fmt}_detailed_stats.csv")
    if stat:
        d = d[d.stat.eq(stat)]
    return clean_records(d)


@app.get("/api/{fmt}/detailed-stats/categories")
def detailed_stats_categories(fmt: str):
    check_format(fmt)
    d = read(f"{fmt}_detailed_stats.csv")
    return clean_records(d[["stat", "stat_label"]].drop_duplicates())


@app.get("/api/teams/master")
def teams_master():
    return clean_records(_TEAM_MASTER)


@app.get("/api/t20_wc/editions")
def t20_wc_editions():
    return clean_records(read("t20_wc_editions.csv").sort_values("year"))


@app.get("/api/wtc/finals-officials")
def wtc_finals_officials():
    return clean_records(read("wtc_finals_officials.csv"))


@app.get("/api/wtc/notable-partnerships")
def wtc_notable_partnerships():
    return clean_records(read("wtc_notable_partnerships.csv"))


@app.get("/api/wtc/umpire-appearances")
def wtc_umpire_appearances():
    return clean_records(read("wtc_umpire_appearances.csv"))


@app.get("/api/wtc/points-tables")
def wtc_points_tables(cycle: str | None = None):
    d = read("wtc_points_tables.csv")
    if cycle:
        d = d[d.cycle.eq(cycle)]
    return clean_records(d.sort_values(["cycle", "final_position"]))


@app.get("/api/wtc/venues")
def wtc_venues(cycle: str | None = None):
    d = read("wtc_venues.csv")
    if cycle:
        d = d[d.cycle.eq(cycle)]
    return clean_records(d.sort_values(["cycle", "matches_hosted"], ascending=[True, False]))



@app.get("/api/statistics/overview")
def overview():
    editions = read("tournament_editions.csv")
    counts = {}
    for fmt, meta in FORMATS.items():
        m = read(meta["matches"])
        counts[fmt] = {"label": meta["label"], "matches": len(m),
                       "editions": int(editions[editions.tournament == meta["label"]].shape[0])}
    return {"formats": counts, "total_editions": len(editions),
            "total_matches": sum(v["matches"] for v in counts.values())}


# ===== Overall Analysis (cross-format) =====
# Category-name classifier shared by the curated {fmt}_records.csv leaderboards - these
# are free-text category names (e.g. "Best Bowling Average (min 500 balls)") rather than
# a fixed taxonomy, so this is keyword-based. Order matters: bowling is checked first
# since e.g. "Best Bowling Average" contains the substring "average" too.
_EXCLUDE_CAT_SUBSTR = ["team total", "successful", "partnership", "match aggregate",
                       "tied match", "prize", "umpired", "dismissals", "catches", "matches"]


def _classify_category(cat):
    n = norm(cat)
    if any(k in n for k in _EXCLUDE_CAT_SUBSTR):
        return None
    if "wicket" in n or "bowling" in n or "economy" in n:
        return "bowling"
    if "run" in n or "score" in n or "average" in n or "centur" in n or "fift" in n or "six" in n:
        return "batting"
    return None


# {fmt}_detailed_stats.csv already has a clean taxonomy (see scripts/10_load_detailed_stats.py)
# so this is a direct lookup rather than keyword-matching.
_DETAILED_STAT_KIND = {
    "most_runs": "batting",
    "most_wickets": "bowling", "best_bowling_innings": "bowling", "best_bowling_match": "bowling",
    "best_economy_career": "bowling", "best_economy_innings": "bowling", "most_runs_conceded": "bowling",
    "most_five_wicket_hauls": "bowling", "most_ten_wicket_hauls": "bowling", "most_wickets_series": "bowling",
}

_PLAYER_TEAM_RE = re.compile(r"^(.*)\s+\(([^)]+)\)\s*$")


@app.get("/api/overview/insights")
def overview_insights():
    """One headline card per format: editions/matches/teams counts, the most-titled team,
    the reigning champion, the #1 name on that format's own "Most Runs" / "Most Wickets"
    leaderboard, and (where the format's records file has them) the highest individual
    score, best bowling figures and highest team total ever recorded - the same numbers a
    visitor would otherwise have to open 4-5 different pages per format to find."""
    ed = read("tournament_editions.csv")
    out = []
    for fmt, meta in FORMATS.items():
        sub = ed[ed.tournament == meta["label"]].sort_values("year")
        title_counts = sub.winner.value_counts()
        top_team = title_counts.index[0] if len(title_counts) else None
        top_titles = int(title_counts.iloc[0]) if len(title_counts) else 0
        reigning = sub.iloc[-1] if len(sub) else None
        m = read(meta["matches"])
        teams_count = len(set(m.team1.dropna()) | set(m.team2.dropna()))

        def top_of(rec_df, needle):
            r = rec_df[rec_df.category.map(norm).str.contains(needle, na=False) & rec_df["rank"].eq(1)]
            return None if r.empty else r.iloc[0]

        def best_of(rec_df, name_variants):
            # Matches one of several category-name spellings (formats don't all name the
            # same stat identically) and, for WTC where the same category/rank repeats once
            # per cycle, keeps whichever cycle's figure is numerically the largest.
            hits = rec_df[rec_df["rank"].eq(1) & rec_df.category.map(norm).isin([norm(v) for v in name_variants])]
            if hits.empty:
                return None
            hits = hits.assign(_v=pd.to_numeric(hits.value, errors="coerce"))
            return hits.sort_values("_v", ascending=False).iloc[0]

        try:
            rec = read(f"{fmt}_records.csv")
        except HTTPException:
            rec = None
        top_scorer = top_wkt = highest_score = best_bowling = highest_total = None
        if rec is not None:
            top_scorer, top_wkt = top_of(rec, "most runs"), top_of(rec, "most wickets")
            highest_score = best_of(rec, ["Highest Individual Score"])
            best_bowling = best_of(rec, ["Best Bowling Figures (innings)", "Best Bowling (Innings)"])
            highest_total = best_of(rec, ["Highest Team Total"])

        out.append({
            "format": fmt, "label": meta["label"],
            "editions": int(len(sub)), "matches": int(len(m)), "teams": teams_count,
            "top_team": top_team, "top_team_titles": top_titles,
            "reigning_champion": reigning.winner if reigning is not None else None,
            "reigning_champion_year": int(reigning.year) if reigning is not None else None,
            "top_scorer": top_scorer.player_team if top_scorer is not None else None,
            "top_scorer_value": top_scorer.value if top_scorer is not None else None,
            "top_wicket_taker": top_wkt.player_team if top_wkt is not None else None,
            "top_wicket_taker_value": top_wkt.value if top_wkt is not None else None,
            "highest_score": highest_score.player_team if highest_score is not None else None,
            "highest_score_value": highest_score.value if highest_score is not None else None,
            "best_bowling": best_bowling.player_team if best_bowling is not None else None,
            "best_bowling_value": best_bowling.detail if best_bowling is not None else None,
            "highest_total": highest_total.player_team if highest_total is not None else None,
            "highest_total_value": highest_total.value if highest_total is not None else None,
        })
    return out


@app.get("/api/overview/countries")
def overview_countries():
    """Every team that has played at least one match in any of the 4 formats - powers
    the country dropdown on the Overall Analysis page's key-players section."""
    countries = set()
    for meta in FORMATS.values():
        m = read(meta["matches"])
        countries |= set(m.team1.dropna()) | set(m.team2.dropna())
    return sorted(countries)


def _name_identity(name):
    """Splits a player name into (surname, initials) for de-duplication - see bump() below."""
    parts = str(name).strip().split()
    if not parts:
        return "", ""
    return parts[-1].casefold(), "".join(p[0] for p in parts[:-1]).upper()


def _initials_compatible(a, b):
    if not a or not b:
        return True
    return a == b or a.startswith(b) or b.startswith(a)


@app.get("/api/overview/key-players")
def overview_key_players(country: str):
    """A country's standout players, consolidated into ONE card per real player across
    all 4 formats (not one card per format), split into Batsmen / Bowlers / All-rounders.
    Role is derived, not stored anywhere - inferred from which kind of record category a
    player shows up in (batting-only -> Batsman, bowling-only -> Bowler, both -> All-rounder).

    Sources, broadest to narrowest:
    1. {fmt}_records.csv - curated top-5/6 leaderboards, all 4 formats.
    2. {fmt}_detailed_stats.csv - fuller top-20 Statsguru-style leaderboards, all 4 formats.
    3. wtc_batting/bowling_stats_{cycle}.csv - real per-player stats for all 3 WTC cycles
       (207 players for 2019-21's full roster; 50/48 and 10/10 leaderboard-cuts for
       2021-23/2023-25 respectively - see 05_clean_wtc.py for why), so WTC nations get
       noticeably more than just the top few record-book names, most fully for 2019-21.

    De-duplication: source (1) spells names in full ("Sachin Tendulkar"), source (2) uses
    ESPNcricinfo Statsguru's initials style ("SR Tendulkar") - the same real player would
    otherwise show up twice. Names are grouped by (surname, initials) where the initials
    just need to be prefix-compatible ("S" vs "SR") rather than identical, which resolves
    the overwhelming majority of real duplicates. This can't perfectly disambiguate two
    genuinely different players who share both a surname and an initial - a known,
    acceptable edge case at this data granularity.
    """
    target = norm(country)
    full_to_abbr = dict(zip(_TEAM_MASTER.full_name, _TEAM_MASTER.abbreviation)) if not _TEAM_MASTER.empty else {}
    full_to_abbr.setdefault("Scotland", "SCO")  # T20 WC detailed-stats uses "SCOT"; team_master has "SCO"
    aliases = {target}
    abbr = full_to_abbr.get(country)
    if abbr:
        aliases.add(norm(abbr))
    if target == "scotland":
        aliases.add("scot")
    # The WTC per-player stats files label teams with their own short codes, two of which
    # don't match team_master's abbreviation ("BDESH" not "BAN", "INDIA" not "IND").
    # Without these, Australia/England/South Africa etc. silently matched nothing there.
    _WTC_TEAM_CODES = {"bangladesh": "bdesh", "india": "india"}
    wtc_aliases = set(aliases) | {_WTC_TEAM_CODES.get(target, "")} - {""}

    groups = []  # list of {surname, initials, display_name, batting, bowling, best_rank, formats:set, achievements:[]}

    def find_or_create(name):
        surname, initials = _name_identity(name)
        for g in groups:
            if g["surname"] == surname and _initials_compatible(g["initials"], initials):
                if len(name.strip()) > len(g["display_name"]):  # prefer the more fully-spelled-out name
                    g["display_name"] = name.strip()
                if len(initials) > len(g["initials"]):
                    g["initials"] = initials
                return g
        g = {"surname": surname, "initials": initials, "display_name": name.strip(),
             "batting": 0, "bowling": 0, "best_rank": 999, "formats": set(), "achievements": []}
        groups.append(g)
        return g

    def bump(name, fmt, label, category, rank, value, kind):
        g = find_or_create(name)
        val_clean = None if pd.isna(value) else value
        dup_key = (fmt, norm(category), rank, val_clean)
        # The curated records file and the fuller detailed-stats file occasionally report
        # the exact same underlying record (same format/category/rank/value) - without this
        # check it would show up twice in one player's achievement list.
        if any((a["format"], norm(a["category"]), a["rank"], a["value"]) == dup_key for a in g["achievements"]):
            return
        g[kind] += 1
        g["best_rank"] = min(g["best_rank"], rank)
        g["formats"].add(fmt)
        g["achievements"].append({"format": fmt, "format_label": label, "category": category,
                                   "rank": rank, "value": val_clean})

    for fmt, meta in FORMATS.items():
        try:
            rec = read(f"{fmt}_records.csv")
        except HTTPException:
            rec = None
        if rec is not None:
            for _, r in rec.iterrows():
                kind = _classify_category(r.get("category"))
                if not kind:
                    continue
                m = _PLAYER_TEAM_RE.match(str(r.get("player_team", "")).strip())
                if not m or norm(m.group(2)) != target:
                    continue
                rank = int(r["rank"]) if pd.notna(r.get("rank")) else 999
                bump(m.group(1), fmt, meta["label"], r.get("category"), rank, r.get("value"), kind)

        try:
            det = read(f"{fmt}_detailed_stats.csv")
        except HTTPException:
            det = None
        if det is not None:
            for _, r in det.iterrows():
                kind = _DETAILED_STAT_KIND.get(r.get("stat"))
                if not kind:
                    continue
                team_col = r.get("Team") if "Team" in det.columns else None
                player_raw = str(r.get("Player", "")).strip()
                if pd.notna(team_col) and team_col:
                    if norm(team_col) != target:
                        continue
                    name = player_raw
                else:
                    m = _PLAYER_TEAM_RE.match(player_raw)
                    if not m or norm(m.group(2)) not in aliases:
                        continue
                    name = m.group(1)
                rank = int(r["rank"]) if pd.notna(r.get("rank")) else 999
                value = r.get("Runs") if kind == "batting" else (r.get("Wkts") if pd.notna(r.get("Wkts")) else r.get("Econ"))
                bump(name, fmt, meta["label"], r.get("stat_label"), rank, value, kind)

    # Broaden beyond the leaderboards using each WTC cycle's real batting AND bowling
    # figures per player (not just record-book names) - since both sides exist per player,
    # this is also the only source that can identify a genuine all-rounder from actual
    # output rather than from the much weaker "happens to appear in both a batting and a
    # bowling leaderboard" signal. Depth varies by cycle: 2019-21 covers every player who
    # featured (207), while 2021-23 (50/48) and 2023-25 (10/10, see 05_clean_wtc.py for why
    # that cycle's cut is smaller) are leaderboard-sized cuts - so this picks up more
    # non-record-book players for the earlier cycles than the later ones, which is an
    # accurate reflection of the underlying data's depth, not a bug.
    for cycle_suffix in ["2019_2021", "2021_2023", "2023_2025"]:
        cycle_label = cycle_suffix.replace("_", "-")
        try:
            wb = read(f"wtc_batting_stats_{cycle_suffix}.csv")
            wl = read(f"wtc_bowling_stats_{cycle_suffix}.csv")
        except HTTPException:
            continue
        if "team" not in wb.columns:
            continue
        both = wb[["player", "team", "runs"]].merge(wl[["player", "team", "wkts"]], on=["player", "team"], how="outer")
        both = both[both.team.map(norm).isin(wtc_aliases)]
        both["runs"] = pd.to_numeric(both.runs, errors="coerce").fillna(0)
        both["wkts"] = pd.to_numeric(both.wkts, errors="coerce").fillna(0)
        for _, r in both.iterrows():
            runs, wkts = r["runs"], r["wkts"]
            # Genuine all-rounder: substantial output with BOTH bat and ball across the
            # 2-year cycle (300+ runs and 10+ wickets). Lower bars were tried and let
            # specialist bowlers through on tail-end runs alone - at 150/5, Starc, Lyon and
            # Cummins all registered as "all-rounders", which is plainly wrong. Otherwise
            # credit only the discipline the player actually contributed in.
            is_ar = runs >= 300 and wkts >= 10
            if is_ar or runs >= 250:
                bump(r["player"], "wtc", FORMATS["wtc"]["label"], f"{cycle_label} cycle runs", 999, runs, "batting")
            if is_ar or wkts >= 8:
                bump(r["player"], "wtc", FORMATS["wtc"]["label"], f"{cycle_label} cycle wickets", 999, wkts, "bowling")

    out = {"batsmen": [], "bowlers": [], "all_rounders": []}
    for g in groups:
        role = "all_rounders" if (g["batting"] and g["bowling"]) else ("bowlers" if g["bowling"] else "batsmen")
        g["achievements"].sort(key=lambda a: a["rank"])
        out[role].append({"player": g["display_name"], "formats": sorted(g["formats"]),
                           "best_rank": g["best_rank"], "achievements": g["achievements"]})
    for role in out:
        out[role].sort(key=lambda p: (p["best_rank"], -len(p["achievements"])))
        out[role] = out[role][:10]
    return out
