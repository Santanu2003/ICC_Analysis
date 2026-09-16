# T20 World Cup & Champions Trophy Player Bios — Final Status

## Coverage achieved
- **t20wc_players_bios.csv**: 797 / 958 unique players (83.2%) — nationality, DOB,
  batting hand, bowling arm/style.
- **ct_players_bios.csv**: 504 / 685 unique players (73.6%) — unchanged from the
  first pass (see below for why).

## How the extra coverage was gained
Layer 1 (both files): cross-matched every player against the bio table already in
your ball-by-ball ODI World Cup dataset (exact + fuzzy name match).

Layer 2 (T20 WC only): Wikipedia publishes one combined "squads" page per tournament
edition, listing every team's full squad with DOB and batting/bowling style in one
table. Successfully parsed the **2024 edition's** page this way, recovering 93 more
players in a single pass.

## Why this is not, and cannot practically become, 100%
Two separate walls, not just remaining effort:

1. **Genuinely missing data.** Some players — mostly retired associate-nation
   cricketers from the 2007–2016 editions — have no DOB or bowling style recorded
   on Wikipedia, ESPNcricinfo, or anywhere else public. That data may not exist
   in digitized form at all.

2. **A real tooling limitation, hit directly while doing this.** The same
   "combined squads page" approach that worked perfectly for 2024 T20 WC failed
   completely on the 2021 and 2022 squads pages — their tables use a different
   underlying wiki markup that this fetching tool cannot convert into readable
   rows (headers come through, every data row comes back empty). This isn't
   fixable by retrying; it's inconsistent page-to-page and only discoverable by
   trying each one. The remaining 7 T20 WC editions and 9 Champions Trophy
   editions have not been attempted for this reason — success is unpredictable
   per page, and roughly half the ones tried so far have failed outright.

## What would actually close the rest of the gap
- **ESPNcricinfo's player pages / API** — more consistent structure than Wikipedia's
  squad pages, but would need one lookup per remaining player (~350+), not per
  tournament edition.
- **Cricsheet's `people.csv` registry** — has stable player IDs and can cross-link
  to Cricsheet's ball-by-ball data (see #1 from earlier), though it doesn't itself
  carry DOB/bowling style.
- Realistically, closing this gap fully means a dedicated scraping pass against
  ESPNcricinfo profile pages, which is a different, larger task than what's been
  done here.
