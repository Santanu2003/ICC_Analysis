# Raw data sources

All original filenames preserved under `data/raw/`. This maps each to what it actually
contains, since several were ambiguously named (`archive__N_.zip`) in the upload.

| Folder | Contents | Used for |
|---|---|---|
| `archive__6_/` | `icc_dataset.xlsx` - one row per ODI WC / T20 WC / Champions Trophy edition (winner, runner-up, semis, POTM) | `tournament_editions.csv` (master, minus WTC) |
| `archive__7_/` | Champions Trophy match results + player lists, all 10 editions | `champions_trophy_matches.csv`, `champions_trophy_players.csv` |
| `archive__9_/` | 13 per-year Excel workbooks, ODI WC 1975-2023, each with a Results sheet + group/points-table sheets | `odi_wc_matches.csv`, `odi_wc_standings.csv` |
| `archive__10_/` | T20 WC match results (scores + team rankings) + full player lists, all 9 editions | `t20_wc_matches.csv`, `t20_wc_players.csv` |
| `archive__11_/` | T20 WC all-time top-5 records (runs/wickets/bowling/totals) + finals summary | `t20_wc_{most_runs,most_wickets,...}.csv`, `t20_wc_editions.csv` |
| `archive__12_/` | Ball-by-ball ODI dataset (matches/innings/overs/players/teams/venues) - not tournament-scoped past 2019, corrupted `matches.csv` export | *not used* - documented as a future-work candidate |
| `archive__13_/` | WTC 2019-21 cycle - deep Statsguru-style export (matches, batting, bowling, partnerships, highest totals/aggregates, points table, venues) | `wtc_matches.csv`, `wtc_points_tables.csv`, `wtc_venues.csv`, `wtc_{batting,bowling}_stats_2019_2021.csv`, synthetic `wtc_records.csv` rows for this cycle |
| `archive__14_/` | WTC 2019-21 batting/bowling averages (matches archive_13's player count) | cross-checked against archive_13, not separately loaded |
| `WTC_2021-2023_Dataset/` | WTC 2021-23 cycle - matches, points table, venues, top-5 records | `wtc_matches.csv`, `wtc_points_tables.csv`, `wtc_venues.csv`, `wtc_records.csv` rows |
| `WTC_2023-2025_Dataset/` | WTC 2023-25 cycle - same shape as above | same |
| `1788940123585_icc_cwc.csv` | ODI WC team-innings-level data, alternate format | *not used* - archive_9's per-year Excel files are cleaner and cover the same ground |

## Known raw-data quirks fixed during cleaning

- `WTC_2023-2025_Dataset/Matches.csv` has a few `Result_Summary` values with an
  unescaped mid-sentence comma, breaking the column count - repaired by rejoining the
  overflow field (see `scripts/05_clean_wtc.py`).
- Both raw WTC folders' `Match_Date` is a day-range string (`"4-8 Aug 2021"`, or
  cross-month `"29 Nov-3 Dec 2021"`) that `pandas.to_datetime` silently mis-parses into
  garbage dates/times - a dedicated regex parser extracts the correct start date.
- `archive__11_/*.csv` (T20 WC records) each end with a footnote row repeated across
  every column ("Qualification: ... Last updated ...") - filtered out by content match,
  not row length (real score values can be longer than the footnote's early tokens).
- `archive__13_/(2) batting_runs.csv` and `(3) Bowling.csv` encode team as `"Name (TEAM)"`
  inside the player field with no separate column, and have no average column - both are
  split out / computed in `scripts/05_clean_wtc.py`.

## Sept 2026 gap-fill load (`scripts/09_load_gap_fill_datasets.py`)

Raw sources under `data/raw/gap_fill_2026-09-11/`. This pass closed the consistency gaps
between formats — every one of ODI World Cup / T20 World Cup / Champions Trophy / World
Test Championship now has the same 3 sections: a player list, a records leaderboard, and
group/league standings.

| Folder | Contents | Used for |
|---|---|---|
| `odi_wc_players_1975_2023_merged.csv` | Every ODI WC squad, 1975-2023, with DOB/batting/bowling style/first-class team | `odi_wc_players.csv` — **ODI WC had no player list at all before this** |
| `records_all_tournaments/` | Records leaderboards for ODI WC + Champions Trophy (new), and T20 WC restructured into the same shape | `odi_wc_records.csv`, `champions_trophy_records.csv` (**both new — neither format had a records file before**), `t20_wc_records.csv` (replaces 5 separate per-category files, which are deleted) |
| `standings_t20_ct/` | Group-stage standings for T20 WC (9 editions) and Champions Trophy (7 editions with a group stage; 1998/2000 were pure knockouts and are correctly absent) | `t20_wc_standings.csv`, `champions_trophy_standings.csv` (**both new**); `odi_wc_standings.csv` reshaped to the same column set |
| `player_bios_v2_final/`, `player_bios_v1/` | DOB/nationality/bowling style, cross-matched from the ODI ball-by-ball player table + one parsed Wikipedia squads page (2024 T20 WC) | Merged onto `t20_wc_players.csv` (88.5% of rows matched) and `champions_trophy_players.csv` (80.8% of rows matched) |
| `wtc_extras/` | Finals match officials, a few standout partnerships, umpire cycle-appearance counts | `wtc_finals_officials.csv`, `wtc_notable_partnerships.csv`, `wtc_umpire_appearances.csv` — small, WTC-only, genuinely new |
| `team_venue_master/` | Curated team master (26 teams: full name/abbreviation/region) + venue master/name-mapping + an abbreviation lookup JSON | `team_master.csv` etc. — merged onto `/api/{fmt}/teams` for an abbreviation tag; **not** yet used to rewrite team/venue names retroactively in existing match files |

### Known gaps still open after this load
- **WTC still has no *browsable* squad-list page** — unlike the other 3 formats, whose
  player lists cover a genuine full roster. WTC's per-player batting/bowling data (added
  in full for 2019-21, and partially for 2021-23/2023-25 in the Sept 2026 3rd batch, see
  below) feeds the cross-format key-players overview instead, but showing 2021-23's
  50-player or 2023-25's 10-player leaderboard cuts as if they were full squad lists would
  misrepresent those two cycles' actual depth.
- **T20 WC / Champions Trophy player bios were ~74-83% complete for batting style and
  ~51-54% for bowling style by unique player** (as of the Sept 2026 3rd batch). A Sept
  2026 follow-up pass (`scripts/12_cross_fill_player_styles.py`) cross-referenced each
  unmatched player against their OWN other tournament appearances — the same real person
  often also played the ODI World Cup, or the other of T20 WC/Champions Trophy, under a
  bio that DID have the style recorded. That pass is safety-gated: a name is only used to
  fill a gap if every non-null value on record for that name agrees exactly across all
  three datasets; names with conflicting values (a handful, e.g. AB de Villiers is logged
  as both "Wicket-keeper" and "Medium seam" for bowling depending on which dataset
  recorded which role) are left untouched rather than guessed. Net effect:
  - T20 WC: batting 84.3% → 86.8%, bowling 53.5% → 71.2%
  - Champions Trophy: batting 80.9% → 86.5%, bowling 51.1% → 76.0%
  - ODI WC: bowling 95.5% → 96.0% (batting was already 100%)

  What's left after that pass (T20 WC batting 13.2%/bowling 27.7% still missing;
  Champions Trophy batting 13.5%/bowling 22.4% still missing) is players who never
  appeared in either of the other two datasets under a matching name AND were never in
  the original bio source — genuinely outside what's derivable from data already in this
  project (578 unique players still missing bowling style, 357 missing batting, across
  both formats combined). Same associate-nation/T20-only-specialist concentration as
  before, concentrated in T20 WC 2026 in particular (157 of the missing-bowling rows).
  Closing the rest needs an ESPNcricinfo-profile scrape or Cricsheet's `people.csv`.
- **`dob` had the same gap and got the same treatment** (`scripts/14_cross_fill_dob.py`,
  identity = name+team, same as the style cross-fill). Unlike style, DOB is genuinely
  inconsistent between sources for the same real player (Adam Milne, NZ: 1992-04-30 in
  the ODI data vs 1992-04-13 in the T20 data — a source data-entry discrepancy, not two
  different players) so DOB was deliberately never used as the *matching* key anywhere in
  this project, only as a value to fill once identity is established some other way. 116
  identities hit exactly this kind of internal disagreement and were left unfilled rather
  than picking one date arbitrarily. Net effect: T20 WC dob 83.6% → 85.7%, Champions
  Trophy 80.8% → 86.5%. Filled values are written in whichever date convention that
  file's own column already uses (ODI: "15 July 1950"; T20/Champions Trophy: ISO
  "YYYY-MM-DD") so no column ends up with mixed formats.
- **`team_master.csv` doesn't cover every associate nation** — USA and PNG (both T20 WC
  participants) have no entry, so they don't get an abbreviation tag. Everything else
  matched, including a few spelling variants (e.g. "United Arab Emirates" vs "U.A.E.")
  handled via a small alias table in `backend/app/main.py`.
- **`venue_master.csv` / `venue_name_mapping.csv` are loaded but inert** — they're a
  ready-made canonical venue list + raw-string-to-canonical mapping, but nothing in the
  existing match/edition files has been rewritten to use them yet. Worthwhile follow-up
  if venue names ever need to be deduplicated/standardized for display.
- ODI WC "Best Bowling Figures" rank 5 and Champions Trophy "Highest Team Total" ranks
  4-5 carry a data-quality caveat from the source itself (see
  `data/raw/gap_fill_2026-09-11/records_all_tournaments/README.txt`) — usable, just
  flagged as not independently cross-checked against ESPNcricinfo Statsguru.

## Sept 2026 gap-fill load, 2nd batch (`scripts/10_load_detailed_stats.py`)

Raw sources under `data/raw/gap_fill_2026-09-13/`, one folder per format (`odi_wc_records_detailed/`,
`t20_wc_records_detailed/`, `champions_trophy_records_detailed/`, `wtc_records_detailed/`).
ESPNcricinfo Statsguru-style records — most runs/wickets (career), best bowling figures
(innings, and match for WTC), career/innings economy rates, most runs conceded in an
innings, most five-/ten-wicket hauls, most wickets in a series. Output: one
`{fmt}_detailed_stats.csv` per format, exposed via `/api/{fmt}/detailed-stats` and shown
as a new "Detailed Statsguru-style records" section on every format's Players & Records
page, alongside (not replacing) the curated leaderboard from the first gap-fill batch.

Column names were normalised during load since the 4 source folders didn't spell the
same stat consistently — e.g. ODI WC/T20 WC used bare `4`/`5`/`10` for wicket-haul
thresholds where Champions Trophy/WTC used `4w`/`5w`/`10w`; date/match-ID columns were
`MatchDate`/`ODI#`/`Test#`/`Scorecard` depending on source. All normalised to a shared
set (`4w`/`5w`/`10w`, `Match Date`, `Match ID`, `Series`) so the same category renders
identically regardless of which format it came from.

8 of the 10 categories are common to all 4 formats; `most_wickets_series` only applies
to odi_wc/t20_wc/champions_trophy (WTC doesn't group matches into a "series" the same
way), and `best_bowling_match`/`most_ten_wicket_hauls` are WTC-only (only meaningful
across a Test match's 2 innings). The frontend's `DetailedStatsGrid` builds each
category's table columns dynamically from whatever fields are actually populated,
rather than hand-coded per format, since the underlying column sets differ by stat type
(batting vs bowling-career vs per-innings) in a way that's consistent across formats but
not across categories.

### Known caveats carried over from the source
- Both README files (`odi_wc_records_detailed/` doesn't have one; `champions_trophy_records_detailed/README.md`
  and `wtc_records_detailed/README.md` do) note these are **partial lists** (top ~10-45
  entries as visible in the ESPNcricinfo screenshots they were transcribed from on
  12 Sep 2026), not complete all-time lists, and a few rows/columns may be incomplete
  where a screenshot was cut off or obscured by ads/UI elements.
- Player names in this dataset use ESPNcricinfo's compact form (e.g. "CH Gayle (WI)"),
  which differs from the fuller "Chris Gayle (West Indies)" style used in the first
  batch's `{fmt}_records.csv` — both are faithful to their own source and haven't been
  reconciled into one naming convention.

## Overall Analysis page (`/api/overview/*` in `backend/app/main.py`)

Cross-format page, reachable straight from the Home sidebar. Two pieces:

- **Key insights** (`/api/overview/insights`) — one card per format: edition/match
  counts, the most-titled team (from `tournament_editions.csv`'s winner column), and
  the #1 name on that format's own "Most Runs"/"Most Wickets" leaderboard. Pure
  aggregation, no new data.
- **Key players by country** (`/api/overview/countries`, `/api/overview/key-players`) —
  pick a country, see its standout players across all 4 formats split into
  Batsmen/Bowlers/All-rounders. **Role isn't a stored field anywhere** — there's no
  "position" column in any source dataset — it's inferred per player from which *kind*
  of record category they show up in for that country: appearing only in batting-type
  categories (Most Runs, Highest Score, batting average, centuries...) → Batsman;
  only bowling-type (Most Wickets, bowling average/economy, 5-/10-wicket hauls...) →
  Bowler; both → All-rounder. Team/match-level categories (Highest Team Total, Highest
  Partnership, Most Matches Umpired, etc.) are excluded from this classification since
  they don't identify a single player's skill.

  This pulls from three sources, broadest to narrowest:

  1. `{fmt}_records.csv` — curated top-5/6 leaderboards, all 4 formats (matched by the
     "Name (Country)" suffix those use).
  2. `{fmt}_detailed_stats.csv` — fuller top-20 Statsguru-style leaderboards, all 4
     formats (matched by a `Team` column where present, otherwise a "Name (ABBR)" suffix
     resolved through `team_master.csv`'s abbreviation column).
  3. `wtc_batting/bowling_stats_2019_2021.csv` — real per-player figures for all 207
     players who appeared in that cycle, not just leaderboard-toppers. This is the only
     place in the entire dataset with **both** batting and bowling output per player, so
     it is also the only source that can identify an all-rounder from actual performance
     rather than the much weaker "appears in both a batting and a bowling leaderboard"
     signal. Thresholds: 300+ runs **and** 10+ wickets for all-rounder; 250+ runs or
     8+ wickets to be credited in a single discipline. Lower bars were tested and
     rejected — at 150 runs / 5 wickets, Starc, Lyon and Cummins all registered as
     "all-rounders" off tail-end runs alone.

     Note this file labels teams with its own codes, two of which differ from
     `team_master.csv` (`BDESH` not `BAN`, `INDIA` not `IND`); those are aliased
     explicitly. Before that was handled, Australia/England/South Africa matched nothing
     here at all.

  **Ruled out: the ball-by-ball archive.** `data/raw/archive__12_/` (157k deliveries) looks
  like it could yield real per-player World Cup aggregates, and runs/wickets *are* derivable
  from its `score` column. It cannot be used: joining deliveries → overs → innings → matches
  and filtering to the 12 genuine World Cup editions returns **zero balls**. Its coverage is
  entirely World Cup *Qualifiers*, *League 2*, Asia Cup and bilateral series from 2021–23 —
  no main-event World Cup match is present. This was verified directly, not assumed.

  **Name de-duplication.** Source (1) spells names in full ("Sachin Tendulkar"); source (2)
  uses ESPNcricinfo's initials style ("SR Tendulkar"). The same real player would otherwise
  appear twice. Names are therefore grouped by `(surname, initials)` where the initials only
  need to be *prefix-compatible* ("S" vs "SR") rather than identical, and the most
  fully-spelled-out variant wins as the display name. This resolves the overwhelming
  majority of real duplicates. It cannot perfectly disambiguate two genuinely different
  players sharing both a surname and a leading initial — a known, accepted edge case at this
  data granularity.

  Results are **consolidated per player across all 4 formats** (one card per real person,
  listing every format they have data in), not one card per player-format pair. Identical
  records reported by both source (1) and source (2) — same format, category, rank and
  value — are collapsed so a player's achievement list doesn't repeat itself.

  **Coverage is uneven by design — and cannot currently reach 10/10/10 for every country.**
  The endpoint returns up to 10 per role. What it actually fills, measured against the
  current data:

  | Country | Batsmen | Bowlers | All-rounders |
  |---|---|---|---|
  | India, Australia, England, South Africa, New Zealand, Sri Lanka | 10 | 10 | 1–4 |
  | Pakistan | 9 | 10 | 2 |
  | West Indies | 8 | 10 | 5 |
  | Bangladesh | 5 | 10 | 2 |
  | Afghanistan | 1 | 10 | 0 |
  | Zimbabwe | 1 | 3 | 0 |
  | Ireland, Netherlands, Kenya, U.A.E. | 0 | 3–4 | 0 |
  | Canada, Bermuda, Namibia, Oman, Nepal | 0 | 1 | 0 |
  | P.N.G., Hong Kong, East Africa | 0 | 0 | 0 |

  The ceiling is structural, not a tuning problem. Every batting/bowling source here is a
  **leaderboard** (top 5–6 curated, top 20 detailed) covering all countries at once — so a
  single nation can only ever claim the handful of slots it occupies on those lists. WTC's
  per-cycle batting/bowling files add real per-player figures on top of the leaderboards —
  2019–21 with a full 207-player roster, 2021–23 and 2023–25 as smaller top-N cuts (see the
  Sept 2026, 3rd batch entry below) — which is why Test nations fill out more than
  associate nations, and why 2019–21 still contributes the most of the three. All-rounder
  counts stay low for the same reason: even combined, these files cover players active in
  specific two-year cycles, so only players who featured there can be identified as
  all-rounders from real output.

  Closing this properly needs per-player career aggregates per format (a Statsguru-style
  "all players, all editions" export for ODI WC / T20 WC / Champions Trophy), which is not
  present in any supplied dataset. The lists are shown at their true depth rather than
  padded with players who have no supporting statistic.

## Sept 2026 gap-fill load, 3rd batch (`scripts/05_clean_wtc.py`)

Raw source under `data/raw/gap_fill_2026-09-14/wtc_player_stats/` — real per-player
batting/bowling stats for the 2021-23 and 2023-25 WTC cycles, closing the gap the 1st
batch called out ("WTC has no per-tournament squad-list dataset" / 2019-21 being the only
cycle with real per-player figures). Output: `wtc_batting_stats_2021_2023.csv`,
`wtc_bowling_stats_2021_2023.csv`, `wtc_batting_stats_2023_2025.csv`,
`wtc_bowling_stats_2023_2025.csv`, feeding `/api/overview/key-players` for all 3 cycles
(previously 2019-21 only). Still not exposed as a browsable Squads page for WTC — see
`ARCHITECTURE.md`'s known-gaps list for why.

**The two cycles were not treated equally**, because they didn't hold up equally under
verification (full account in `data/raw/gap_fill_2026-09-14/wtc_player_stats/VERIFICATION_NOTES.md`):
- **2021-23** (50 batters, 48 bowlers): spot-checked against this project's own
  already-verified `wtc_records.csv` entries and against Wikipedia — matched exactly.
  Loaded as delivered.
- **2023-25**: the delivered file's own README flagged 2 issues (a blank stat, one
  value it wanted to correct); checking those surfaced a 3rd, undisclosed one — a row
  marked "confirmed" that in fact disagreed with an independently-sourced table on 5
  fields at once. Given a confidence label that didn't hold up, this cycle was rebuilt
  from scratch from independently corroborated web sources instead (top 10 batters, top
  10 bowlers, each cross-checked against 2+ independent articles) rather than trusting
  the remaining unchecked rows. Smaller than the delivered top-20/top-10, but verified.

**Three corrections applied to `wtc_records.csv`** in the same pass (2023-25 cycle):
Yashasvi Jaiswal's runs (1738 → 1798) and Mitchell Starc's wickets (blank → 77, *not*
the 71 the source suggested) were both confirmed via multiple independent sources. A
third, pre-existing error unrelated to this upload was also found and fixed while
verifying the first two: Usman Khawaja's "Most Runs" line was already wrong before this
batch (20 Mat/39 Inn/1428 runs/39.66 avg → corrected to 19 Mat/37 Inn/1422 runs/41.82
avg; HS 232 was already correct).

---

## 2026-09-16 — T20 World Cup 2026 loaded (10th edition)

The first edition added to this project while it was still the *most recent* tournament
rather than a historical one. India beat New Zealand by 96 runs in the final at the
Narendra Modi Stadium, Ahmedabad (8 March 2026) for their 3rd T20 WC title.

**Raw sources kept in `data/raw/t20_wc_2026/`:**
- `t20_wc_2026_matches.csv` — all 55 matches (user-supplied)
- `t20_wc_2026_standings.csv` — group stage + Super 8 tables, transcribed from
  screenshots of Google's standings panel (user-supplied)
- `t20wc_2026_squads.csv` — all 20 final confirmed squads (300 players), from ICC's
  official post-deadline squad announcement

**What was loaded where:**
| File | Rows added |
|---|---|
| `t20_wc_matches.csv` | 55 (317 → 372) |
| `t20_wc_standings.csv` | 28 (184 → 212) |
| `t20_wc_players.csv` | 300 (1,980 → 2,280) |
| `tournament_editions.csv` | 1 (34 → 35) |

**Normalisation applied to match the 9 prior editions** (the source arrived in a
different shape, so none of this is cosmetic — without it the 2026 rows would not join
or filter alongside the others):
- Team names: `United States` → `USA`, `U.A.E.` → `UAE`. Left unfixed, USA would have
  shown 0 prior World Cups and every USA head-to-head would have been wrong.
- Scores: `148/7` → `148-7`.
- Margins: `won by 3 wickets (3 balls remaining)` → `3 wickets`.
- Grounds: `Eden Gardens, Kolkata` → `Kolkata` (prior editions store city only). Two
  rows had the *country* ("Sri Lanka") in the ground column — blanked, since
  `host_country` already carries that.
- No-result rows: winner `No result` → `no result`, margin → `-`, both matching the 7
  no-results already in the file.
- `team1_total_wcs_participated/won`, `team2_*`, and `team1_win_pct_over_team2` were
  **computed** from this project's own historical data, not copied — same definition as
  every prior edition.

**Validated, not assumed:** every team's M/W/L in the 2026 standings was recomputed
from the 55 match results and reconciled exactly (0 mismatches, both stages). Points
were independently checked against the 2×W + 1×NR rule (0 mismatches) — this is what
explains the odd-looking totals, e.g. Zimbabwe 3W/0L from 4 games = 7 pts, because one
match was a no-result.

**Known gaps in the 2026 data (deliberately left blank rather than guessed):**
- `ground` (city only, matching this file's existing convention) is now filled for all
  55 matches. It initially shipped blank for 26 group-stage rows — the user's source
  didn't carry a venue for them — and was filled in a follow-up pass from ICC's official
  pre-tournament fixture list (25 Nov 2025 schedule announcement), matched by date +
  team pair. Bangladesh was in that original schedule and was later replaced by Scotland
  in the same date/venue slots (see Britannica's account of the Bangladesh security
  dispute) — confirmed against the user's match data before mapping Scotland to
  Bangladesh's original venues. Cross-checked against `host_country` for all 55 rows
  (Colombo/Kandy <-> Sri Lanka, everything else <-> India): 0 contradictions.
  `host_country` was filled for all 55 in the original pass using the edition's
  published venue rule (every Group B match, plus any Group A match involving Pakistan,
  was played in Sri Lanka under the BCCI/PCB neutral-venue agreement; all other
  first-round matches in India).
- `match_no` (the `T20I # NNNN` serial) is blank for all 55 — not in the source.
- `team1_avg_batting_ranking` / `..._bowling_ranking` are blank for all 55 — these come
  from a player-rankings source that has no 2026 coverage in this project.
- `player_of_match` came through on only 4 of 55 source rows, so it is not loaded into
  `t20_wc_matches.csv` (which has no such column anyway); the final's POTM
  (Jasprit Bumrah) is captured in `tournament_editions.csv`.
- 2026 players have `dob` / `nationality` / `bowling_style` blank — the ICC squad
  announcement is a plain name list with no bio fields.
- `t20_wc_records.csv` was **not** touched: it holds all-time leaderboards, and
  recomputing them to include 2026 would need full ball-by-ball or Statsguru data for
  the edition, which isn't available here. One entry already spans "2021-2026".

---

## 2026-09-16 — Batting style fix: T20 WC + Champions Trophy squads, plus a UI bug

Reported by the user: the Squad list page only ever showed a "Bowling style" column,
never batting style, for any format — including ODI World Cup, which has had a
`batting_style` column since the very first load. Investigating turned up two separate,
unrelated causes stacked on top of each other:

1. **Data**: `scripts/09_load_gap_fill_datasets.py`'s `attach_bios()` merges bio data
   from `player_bios_v2_final/t20wc_players_bios.csv` and `player_bios_v1/ct_players_bios.csv`
   onto `t20_wc_players.csv` / `champions_trophy_players.csv`. Those source files carry a
   `Right_Handed_Bat` (True/False) column alongside `Bowling_Style`, but the merge only
   ever selected `Bowling_Style` — `Right_Handed_Bat` was silently dropped. Fixed:
   `attach_bios()` now also maps `Right_Handed_Bat` → `batting_style` ("Right-handed" /
   "Left-handed", same wording `odi_wc_players.csv` already uses) and both files were
   rebuilt from source (running only `build_player_bios()` in isolation — **not** the
   rest of that script's `__main__`, which would have re-run `build_standings()` and
   overwritten the T20 WC 2026 standings added in the previous session).
   `t20_wc_players.csv` and `champions_trophy_players.csv` now have the exact same
   7-column shape as `odi_wc_players.csv` (team, year, player_name, dob, batting_style,
   bowling_style, +nationality/first_class_team respectively).
2. **Frontend**: independently of the above, `PlayerListBrowser` in `main.jsx` (the
   shared Squad list component for all 3 formats) never rendered a batting-style column
   at all — it checked for and displayed `dob` and `bowling_style` only. This meant even
   ODI WC's already-complete batting_style data was invisible on the page. Fixed by
   adding the same `hasBat` presence-check/column pattern already used for the other two
   fields.

Both fixes were necessary — fixing only the data would still show no batting style for
any format (the UI never asked for it); fixing only the UI would show it for ODI WC but
still blank for T20 WC/Champions Trophy (the data wasn't there yet).

**Batting style coverage after the fix**, out of 2,280 T20 WC / 1,155 CT rows
(2026 T20 WC squad included — bio-matched only where a player also appeared in an
earlier edition under the same team, since the bio source itself has no 2026 entries):
- T20 WC: 1,923 filled / 357 blank (batting_style; same ~84% match rate as bowling_style)
- Champions Trophy: 934 filled / 221 blank

No new gaps were introduced — the unmatched rows are the same players already documented
as unmatched for `dob`/`bowling_style` above, not a new shortfall.

---

## 2026-09-16 — Player bio gap-fill from external sources

Following the missing-bio audit, 502 blank `dob` / `batting_style` / `bowling_style`
fields were filled from external sources. Nothing was guessed — every value traces to a
cited source or to another row of this same dataset.

### Source 1: Wikipedia "2026 Men's T20 World Cup squads"
https://en.wikipedia.org/wiki/2026_Men%27s_T20_World_Cup_squads

All 20 squad tables carry No./Player/Date of birth/Batting style/Bowling style. This
closed the single largest gap in the project — the 2026 T20 World Cup, which had been
loaded from an ICC announcement that is a plain name list with no bio fields.

**2026 edition is now complete**: `dob` 300/300, `batting_style` 300/300,
`bowling_style` 270/300. The 30 remaining bowling blanks are correct — Wikipedia marks
those players "—N/a" (specialist batters and keepers who do not bowl).

Matching was strict (exact team + normalised name) with a hand-checked alias map for
name-order variants (e.g. project "Rohid Khan" = Wikipedia "Muhammad Rohid"). All 300
matched with zero unmatched.

> **A bug caught during this work, worth recording.** A first pass used a surname
> fallback when exact matching failed. For UAE it silently matched project "Rohid Khan"
> to Wikipedia's "Sohaib Khan" (the only UAE player with surname "Khan" in the wiki
> list, since Muhammad Rohid's surname parses as "Rohid"), giving two different players
> the same DOB. The fallback was removed entirely and replaced with the explicit alias
> map. If you extend this work, do not reintroduce surname-only matching.

Dates were converted to ISO (`YYYY-MM-DD`) to match the existing convention in
`t20_wc_players.csv` / `champions_trophy_players.csv`.

### Source 2: cross-edition propagation within this dataset
A player's date of birth and batting hand do not change between tournaments, so for any
(team, player) whose bio is known in one edition/format, the value was propagated to
their blank rows in other editions. Guardrails: matched on team **and** normalised name;
where two rows disagreed on a value, that field was skipped rather than picking one
(1,151 such conflicting field-values were left alone — mostly bowling-style wording
variants like "Left-arm fast medium" vs "Left-arm fast-medium", plus a few genuine
same-name-different-player cases). This filled a further 121 fields.

### Result

| File | dob | batting_style | bowling_style |
|---|---|---|---|
| t20_wc_players.csv | 327 → 189 | 301 → 173 | 631 → 452 |
| champions_trophy_players.csv | 156 → 146 | 156 → 147 | 259 → 225 |
| odi_wc_players.csv | 1 → 1 | 0 → 0 | 77 → 73 |

### What is still missing, and why

**319 players still missing all three fields** (173 T20 WC pre-2026, 146 Champions
Trophy), spread across 17 editions from 1998–2024. Two obstacles:

1. Wikipedia's squad pages for most older editions **do not extract their tables**
   through the tooling available here — the 2026 page worked, but e.g. the 2025
   Champions Trophy and 2012 World Twenty20 pages return only column headers with the
   row data stripped. This is an extraction limitation, not missing source data; the
   tables are visible in a browser.
2. Cricsheet's `people.csv` register, the obvious bulk source, contains only cross-site
   **identifiers** — no DOB or style fields. Those live on individual ESPNcricinfo
   player pages, which would require ~319 separate fetches.

Most of the remainder are associate-nation players from older editions. The practical
route to closing it is ESPNcricinfo's player-profile API keyed by the Cricinfo IDs in
Cricsheet's register (`key_cricinfo`), run as a batch job with network access.

**Also still open (unchanged):** `odi_wc_players.csv` has one genuinely missing DOB
(Hamish McLeod, East Africa, 1975). Its remaining 73 blank `bowling_style` values are
believed correct — they are specialist batters who did not bowl, and all have `dob` and
`batting_style` present. See `docs/` audit notes for the full reasoning.

**Note on an unrelated pre-existing inconsistency:** `odi_wc_players.csv` stores dates as
text ("23 July 1950") while the T20/CT files use ISO. This predates this work and was
left as-is rather than silently reformatting a third file.
