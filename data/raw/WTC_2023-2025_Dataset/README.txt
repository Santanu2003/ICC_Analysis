ICC WORLD TEST CHAMPIONSHIP 2023-2025 — DATASET
=================================================

Cycle: 16 June 2023 - 14 June 2025
Champions: South Africa (1st WTC title) | Runners-up: Australia
70 matches (69 league matches across 27 bilateral series + 1 final)

FILES INCLUDED
--------------
1. Matches.csv        - All 70 matches: date, ground, host, teams, result, score
                         summary, and points awarded.
2. Points Table.csv    - Final league standings (verified against the official
                         Wikipedia/ICC/ESPNcricinfo table).
3. WTC_Venues.csv      - Grounds used and number of matches hosted at each,
                         derived from Matches.csv.
4. Records.csv         - Tournament leaderboards: most runs, most wickets, most
                         dismissals (WK & fielder), highest individual scores,
                         best bowling (innings & match), highest average, best
                         bowling average, highest/lowest team totals, prize
                         money, and (partial) highest successful chase.
                         Top-5 lists sourced directly from the official
                         Wikipedia WTC 2023-25 records tables (themselves
                         sourced from ESPNcricinfo Statsguru, last updated
                         14 June 2025).

SOURCES
-------
- https://en.wikipedia.org/wiki/2023%E2%80%932025_World_Test_Championship
- https://en.wikipedia.org/wiki/2025_World_Test_Championship_final
- https://www.espncricinfo.com/series/icc-world-test-championship-2023-2025-1345943
- Individual series/scorecard pages on ESPNcricinfo, Wikipedia, and Wisden,
  cross-checked for venues and results of each bilateral series.

NOTE ON ACCURACY
-----------------
The Points Table.csv and Records.csv figures are taken directly from
Wikipedia's cited WTC 2023-25 tables and are high-confidence.

Matches.csv was reconstructed match-by-match from Wikipedia's results log
(dates, scores and points strings) plus each bilateral series' known
schedule and venues. As with the 2021-23 dataset you uploaded, Wikipedia's
raw results log does not cleanly label which score block belongs to which
team next to each match, so team assignment for some matches was
reconstructed from the accompanying points lines and known series context.
A handful of items carry lower confidence and should be cross-checked
against ESPNcricinfo scorecards before use in any published analysis:
  - Exact ball-by-ball margins/targets for a few matches (marked "(T not
    required)" where the winning margin type was clear but the precise
    chase target was not confirmed).
  - Venues for some shorter, less widely covered series (e.g. Bangladesh
    tour of South Africa Oct 2024; New Zealand tour of Bangladesh 2023;
    Sri Lanka tour of Bangladesh 2024) are the most likely grounds based on
    known international-venue rotation for those boards, not individually
    re-verified per match.
  - Exact over-rate point deductions are shown only where explicitly stated
    in the source; some smaller deductions across the cycle may not be
    reflected to the exact point.
  - Records.csv "Most Wickets" rank 3 (Mitchell Starc) value could not be
    confirmed precisely for this cycle specifically and is left as "n/a" —
    reported cycle-long tallies for Starc were inconsistent across sources
    at the time this file was compiled; cross-check ESPNcricinfo Statsguru
    (series ID 15144) for the exact figure.
  - "Highest Successful Chase" only lists the WTC Final chase (282 by South
    Africa at Lord's), which is confirmed as a headline chase of the cycle;
    a fuller top-5 for this category was not reliably retrievable and was
    not fabricated.

NOT INCLUDED (vs. your 2021-23 reference dataset)
--------------------------------------------------
As with the previous dataset, deep Statsguru-style exports (per-player
batting/bowling aggregates across the whole cycle, partnerships, ICC
ratings snapshots, umpire appointments, WK/fielding tables, etc.) are not
included, since reproducing them accurately by hand isn't reliable. The
direct source for these is:
  https://www.espncricinfo.com/records/tournament/batting-most-runs-career/icc-world-test-championship-2023-2025-15144
(and the equivalent ESPNcricinfo Records pages for bowling, fielding, and
keeping — series ID 15144).
