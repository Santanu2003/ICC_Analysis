GAP 3 — RECORDS/LEADERBOARDS — NOW CONSISTENT ACROSS ALL 4 TOURNAMENTS
=========================================================================

odi_wc_records.csv              - NEW. Most runs (career & single edition), highest
                                   individual score, most wickets, best bowling figures,
                                   highest/lowest team totals, highest successful chase,
                                   highest partnership, best batting/bowling average,
                                   most dismissals (WK & fielder), most matches,
                                   most tournaments played, most matches umpired.
                                   Source: Wikipedia "List of Cricket World Cup records"
                                   (current through the 2023 World Cup).

champions_trophy_records.csv    - NEW. Most runs, highest individual score, most
                                   wickets, best bowling figures, highest team total,
                                   lowest team total, highest match aggregate, highest
                                   successful chase, only tied match, titles summary.
                                   Sources: ICC "in focus" team pages, WION, Guinness
                                   World Records, Statista/ESPNcricinfo charts — current
                                   through the 2025 tournament.

t20_wc_records_consolidated.csv - REBUILT to match the WTC/ODI WC format. Same data
                                   your existing 5 separate files had (most_runs,
                                   most_wickets, best_bowling, highest_totals,
                                   lowest_totals), just restructured into ONE file
                                   with the same Category/Rank/Player/Detail/Value
                                   columns as wtc_records.csv, odi_wc_records.csv, and
                                   champions_trophy_records.csv. You can keep the
                                   original 5 files too — this doesn't replace them,
                                   it standardizes them.

KNOWN GAPS IN THESE FILES (being upfront)
------------------------------------------
- ODI WC "Best Bowling Figures" rank 5 has a note flag — the 5th-best figures entry
  in the Wikipedia table didn't cleanly resolve to a single value in the fetched
  text; treat that one row as unverified until cross-checked.
- Champions Trophy "Highest Team Total" ranks 4-5 (South Africa 2009, England 2017)
  have team/context but the exact score wasn't found in this pass — worth a
  follow-up search if you need those two numbers specifically.
- Neither file has been cross-verified against ESPNcricinfo Statsguru directly
  (both are compiled from Wikipedia + secondary sources) — same caveat as your
  existing WTC records file.

STILL OPEN: GAP 2 (player lists for ODI WC and WTC) — not addressed in this delivery.
