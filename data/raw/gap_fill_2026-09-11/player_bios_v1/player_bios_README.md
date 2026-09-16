# T20 World Cup & Champions Trophy Player Bios

## Method
Cross-matched every unique player name from your T20 WC and Champions Trophy squad
lists against the player bio table already sitting in your ball-by-ball ODI World Cup
dataset (`archive__12_/.../players.csv`), which carries Nationality, Date of Birth,
Batting Hand, Bowling Arm, and Bowling Style. Matching was exact-name first, then a
conservative fuzzy pass (0.88 similarity threshold, spot-checked for false positives —
e.g. correctly linked "Steven Smith" to "Steve Smith") to catch minor name-format
differences.

## Coverage
- **t20wc_players_bios.csv**: 704 / 958 unique players matched (73.5%)
- **ct_players_bios.csv**: 504 / 685 unique players matched (73.6%)

Each row has a `Matched` flag (True/False) so you can filter to what's usable immediately.

## Why ~26% are unmatched — this is real, not a matching failure
The bio source only contains players who appeared in 50-over Cricket World Cup /
ODI cricket. Unmatched players are concentrated in two groups:
1. **Associate-nation players** (Uganda, Oman, Nepal, PNG, USA, Namibia etc.) who
   have never played a full ODI World Cup and simply have no bio record anywhere
   in your existing files.
2. **T20-format specialists** from full-member teams (e.g. Tim David, Josh Inglis,
   Daniel Sams for Australia) who play T20Is but not ODI World Cups, so they never
   appear in the ODI-sourced bio table either — this is a genuine gap in your data,
   not a name-matching miss.

## What would close the remaining gap
Filling the other ~26% needs an external bio source with T20I-specific and
associate-nation player coverage — e.g. ESPNcricinfo player pages or Cricsheet's
`people.csv` registry, which covers T20I/associate players that the ODI-only bio
table never will.
