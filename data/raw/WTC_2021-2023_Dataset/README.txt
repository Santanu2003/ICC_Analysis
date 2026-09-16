ICC WORLD TEST CHAMPIONSHIP 2021-2023 — DATASET
=================================================

Cycle: 4 August 2021 - 11 June 2023
Champions: Australia (1st WTC title) | Runners-up: India
70 matches (69 league matches across 27 bilateral series + 1 final)

FILES INCLUDED
--------------
1. Matches.csv        - All 70 matches: date, ground, host, teams, result, score
                         summary, and points awarded. Compiled from the official
                         Wikipedia results log for the 2021-2023 WTC cycle.
2. Points Table.csv    - Final league standings (verified, matches ICC/ESPNcricinfo).
3. WTC_Venues.csv      - Grounds used and number of matches hosted at each.
4. Records.csv         - Tournament leaderboards and records: most runs, most
                          wickets, most dismissals (WK & fielder), highest
                          individual scores, best bowling (innings & match),
                          highest average, best bowling average, highest/lowest
                          team totals, highest successful chases, and prize money.
                          Sourced directly from Wikipedia's official WTC 2021-23
                          records tables (themselves sourced from ESPNcricinfo
                          Statsguru, last updated 11 June 2023).

NOT INCLUDED (vs. your 2019-21 reference dataset)
--------------------------------------------------
Your uploaded 2019-21 dataset also contained deep Statsguru-style exports:
  - batting_runs.csv / batting_4s6s.csv / batting_6s.csv (every player's
    aggregated batting stats across the whole cycle)
  - Bowling.csv (every player's aggregated bowling stats)
  - Partnership.csv / Highest Partnership.csv
  - Rank_bat.csv / Rank_bowl.csv / Rank_All-round.csv (ICC ratings snapshots)
  - Officials.csv (umpire appointments per match)
  - WK.csv / WK mst-dis-mat.csv / fielding.csv (per-player keeping/fielding)
  - hghst_inn_tot.csv / hghst_mat_aggrt.csv
  - Players.csv, Teams in ENG.csv, Venue_History.csv

These are Statsguru query exports aggregated across ~200+ players and 70
matches. Reproducing them accurately by hand (rather than by scraping
stats.espncricinfo.com directly) isn't something I can do reliably, so I
did not fabricate approximate numbers for them. If you need these files
for the 2021-23 cycle, the direct source is:
  https://stats.espncricinfo.com/ci/engine/records/index.html?id=14028;type=tournament
(replace id=14028 with the correct series ID for 2021-2023, or navigate via
ESPNcricinfo > Records > filter by "ICC World Test Championship 2021-2023")

SOURCES
-------
- https://en.wikipedia.org/wiki/2021%E2%80%932023_World_Test_Championship
- https://en.wikipedia.org/wiki/2023_World_Test_Championship_final

NOTE ON ACCURACY
-----------------
Match winners, dates, grounds, points, and the Records.csv leaderboard are
sourced directly from the cited Wikipedia tables and cross-checked against
known series results. Some Margin/Result_Summary text is condensed from
partial score data (Wikipedia's raw results log omits some team-name labels
next to score lines, which were reconstructed from known series schedules).
For match-by-match exact winning margins, cross-check against ESPNcricinfo
scorecards before using in any published analysis.
