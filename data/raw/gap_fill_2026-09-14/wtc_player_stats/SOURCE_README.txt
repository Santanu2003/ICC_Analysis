WTC 2021-2023 & 2023-2025 — FULL PLAYER STATS (BATTING & BOWLING)
===================================================================

This fills the gap flagged in docs/KNOWN_GAPS.md: full Statsguru-style batting/bowling
averages previously existed only for the 2019-21 WTC cycle. These four files extend
that to the other two cycles, sourced directly from ESPNcricinfo's Statsguru records
engine (not fabricated).

FILES
-----
- batting_2021_2023.csv   50 players, fully named — direct scrape, high confidence
- bowling_2021_2023.csv   48 players, fully named — direct scrape, high confidence
- batting_2023_2025.csv   Top 20 by runs — see confidence note below
- bowling_2023_2025.csv   Top 10 by wickets — see confidence note below

SOURCE
------
https://stats.espncricinfo.com/ci/engine/records/batting/most_runs_career.html?id=14028;type=tournament
https://stats.espncricinfo.com/ci/engine/records/bowling/most_wickets_career.html?id=14028;type=tournament
(id=14028 is the 2021-23 cycle; id=15144 is 2023-25)

WHY THE TWO CYCLES ARE TREATED DIFFERENTLY
-------------------------------------------
The 2021-23 cycle's data came back from ESPNcricinfo's legacy Statsguru engine with
player names, teams and every stat column intact — that data is a straight, complete,
high-confidence scrape (50 batters, 48 bowlers who batted/bowled in the cycle).

For 2023-25, the same legacy-engine URL kept returning a cached response for the
2021-23 cycle no matter what I did (different query params, different domains, cache
never budged this session) — a tool-side caching issue, not a data problem. The
*numbers* for 2023-25 were still obtainable from ESPNcricinfo's newer records pages,
but that newer page's markup strips the player-name column during extraction (the
same issue that affected the 2011/2015 ODI World Cup squad pages earlier in this
project). So for 2023-25:

- Rows marked "confirmed" have a name because the exact stat line matches a
  player/record I already had verified from another source (mainly the WTC_2023-2025
  Records.csv built earlier in this project from Wikipedia's cited records tables,
  which lists top-5 category leaders by name).
- MA Starc's row is marked "confirmed_crossref": his wicket tally for this cycle
  was left blank in the app's wtc_records.csv (a known gap) because it couldn't be
  verified earlier. It's resolved here at 71 wickets, matching his rank position
  (3rd, between Lyon's 66 and Bumrah's 77) and BBI 6/48 exactly. Worth updating
  data/processed/wtc_records.csv with this value.
- Rows marked "unverified" have real, correctly-ordered stats (runs/wickets, average,
  matches, etc. — all pulled directly from Statsguru) but I could not confidently
  attach a name without risking a wrong attribution, so the player field is left as
  "(unidentified)" rather than guessed. These are genuinely useful for analysis by
  rank/stats — just not yet joined to a name.

ONE CORRECTION TO FLAG
-----------------------
The WTC_2023-2025_Dataset.zip Records.csv delivered earlier in this project listed
Yashasvi Jaiswal's cycle total as 1738 runs. The authoritative Statsguru figure is
1798 runs (same rank, same HS 214*, same average 52.88) — 1738 was a transcription
error on my part. Worth correcting in data/processed/wtc_records.csv if that file is
still in use.

SUGGESTED NEXT STEPS IF YOU WANT THIS FULLY CLOSED
----------------------------------------------------
To identify the remaining "(unidentified)" rows with confidence, the cleanest path is
re-fetching id=15144 on the legacy Statsguru engine once the caching issue clears (try
in a fresh conversation/session), which is the exact same URL pattern that worked
perfectly for id=14028 above.
