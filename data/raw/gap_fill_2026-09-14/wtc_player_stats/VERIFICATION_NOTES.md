# Verification notes on this gap-fill batch (2026-09-14)

The source README (`SOURCE_README.txt`) is the uploader's own account of how these 4
files were built. Before loading any of it into the pipeline, each headline claim was
checked against independent web sources (Wikipedia, ESPNcricinfo-sourced news
coverage, ICC-affiliated reporting). Results:

## 2021-2023 batting/bowling (`batting_2021_2023.csv`, `bowling_2021_2023.csv`)
**Trustworthy - loaded as-is.** Spot-checked Joe Root (1915 runs), Nathan Lyon
(88 wickets) against Wikipedia's 2021-2023 WTC infobox - exact match. Spot-checked
Usman Khawaja's full line (17 Mat, 30 Inn, 1621 runs, HS 195*, Ave 64.84) against this
project's own `wtc_records.csv` "Highest Batting Average" category, itself sourced
from Wikipedia's cited records tables earlier in this project - exact match on every
field. The "high-confidence direct scrape" claim for this cycle holds up.

## 2023-2025 batting/bowling (`batting_2023_2025.csv`, `bowling_2023_2025.csv`)
**NOT trustworthy as delivered - NOT loaded. Rebuilt from verified sources instead.**
The source README itself flagged two specific issues (Starc's blank wicket count,
Jaiswal's runs), but checking those two surfaced a **third, undisclosed problem**: a
row the file marks "confirmed" (not "unverified") - Usman Khawaja - disagrees with the
verified Business Standard/ESPNcricinfo-sourced table on five separate fields at once
(Mat 20 vs 19, Inns 39 vs 37, Runs 1428 vs 1422, Ave 39.66 vs 41.82, BF 3211 vs 3168).
That's not a rounding difference or a mid-cycle vs final-tally mismatch - it's a
different player-line entirely being misattributed, and it undermines the file's
"confirmed = correct" labeling for this cycle. Given a confidence flag that didn't
hold on inspection, the rest of this cycle's 20 batting / 10 bowling rows are treated
as unverified rather than spot-checking each one individually.

Instead, `wtc_batting_stats_2023_2025.csv` / `wtc_bowling_stats_2023_2025.csv` were
rebuilt from scratch from independently corroborated sources (see `05_clean_wtc.py`
for the hardcoded tables and citations) - the verified top 10 batters and top 10
bowlers, cross-checked across 2-3 independent articles per list where possible. This
is a smaller cut than the uploaded file's top-20/top-10 (fewer of the lower-ranked
entries could be independently confirmed), but every row that IS included is verified,
not scraped-and-hoped.

### The two specific corrections, both confirmed correct and applied to `wtc_records.csv`:
- **Yashasvi Jaiswal, 2023-25 cycle runs: 1798** (not 1738 as previously in
  `wtc_records.csv`). Confirmed via 3 independent sources (Rajasthan Royals official
  site, Business Standard x2) all agreeing on 1798, HS 214*, Ave 52.88.
- **Mitchell Starc, 2023-25 cycle wickets: 77** (not the 71 the uploaded file
  suggested as its "confirmed_crossref" fix, and not the blank it's replacing).
  Confirmed via 2 independent sources (khelnow.com, cricketcountry.com), both giving
  77 wickets in 19 matches at economy 3.84 - matching every other field in the
  uploaded row exactly except the wickets count itself, which was off by 6.

### A third correction, found incidentally, unrelated to today's upload
While verifying the above two against the Business Standard table, that same table
showed `wtc_records.csv`'s existing "Most Runs" rank-5 entry for the 2023-25 cycle
(Usman Khawaja) was ALSO wrong - and had been since before this gap-fill batch,
built from the same flawed intermediate numbers as today's uploaded file's Khawaja
row (20 Mat, 39 Inn, 1428 runs, Ave 39.66 vs the verified 19 Mat, 37 Inn, 1422 runs,
Ave 41.82 - HS 232 was already correct). Fixed in the same pass since it sits in the
same table as the other two corrections.
