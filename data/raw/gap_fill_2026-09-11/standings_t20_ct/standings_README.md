# T20 World Cup & Champions Trophy Standings

## t20_world_cup_standings.csv
184 rows covering all 9 editions (2007, 2009, 2010, 2012, 2014, 2016, 2021, 2022, 2024).
Columns: Tournament, Year, Stage (First Round / Group Stage / Super Eight / Super 10 / Super 12 / Super 8),
Group, Pos, Seed (pre-tournament seed code where applicable, group stages only), Team, Pld, W, L, T, NR, Pts, NRR.

## champions_trophy_standings.csv
68 rows covering the 7 editions that had a group stage: 2002, 2004, 2006, 2009, 2013, 2017, 2025.
**1998 and 2000 are deliberately excluded** — both were pure single-elimination knockout tournaments
(the event was literally called the "ICC KnockOut Trophy" then) with no group stage or points table at all.
2006 additionally had a "Qualifying Round" (4 lowest-ranked teams, top 2 advanced to the main groups) —
included as its own Stage value.
Columns: Tournament, Year, Stage (Pool / Qualifying Round / Group Stage), Group, Pos, Team, Pld, W, L, T, NR, Pts, NRR.

Source: ESPNcricinfo / Wikipedia tournament pages, cross-checked against each other where both were available.
