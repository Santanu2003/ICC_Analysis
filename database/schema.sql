-- Optional PostgreSQL schema for ICC Tournaments Analytics.
-- The live app runs straight off the CSVs in data/processed/ - this is only
-- an upgrade path for anyone who wants to move off flat files. Mirrors the
-- FIFA World Cup Analytics project's database/ convention.

CREATE TABLE IF NOT EXISTS tournament_editions (
    edition_id TEXT PRIMARY KEY,
    tournament TEXT NOT NULL,
    year INTEGER NOT NULL,
    cycle_label TEXT,
    venue TEXT,
    winner TEXT,
    runner_up TEXT,
    semi_finalists TEXT,
    final_player_of_match TEXT,
    player_of_tournament TEXT
);
CREATE INDEX IF NOT EXISTS idx_editions_tournament ON tournament_editions(tournament);

-- One matches table per format keeps each format's real schema (ODI WC has
-- scores+overs, T20 WC/CT have rankings, WTC has result_type/summary) rather
-- than forcing everything into a lossy lowest-common-denominator table.

CREATE TABLE IF NOT EXISTS odi_wc_matches (
    match_id TEXT PRIMARY KEY,
    year INTEGER NOT NULL,
    stage TEXT,
    match_number INTEGER,
    match_date DATE,
    ground TEXT,
    country TEXT,
    team1 TEXT, team1_score TEXT, team1_wickets TEXT, team1_overs TEXT,
    team2 TEXT, team2_score TEXT, team2_wickets TEXT, team2_overs TEXT,
    winner TEXT, win_margin TEXT, toss TEXT
);

CREATE TABLE IF NOT EXISTS t20_wc_matches (
    match_id TEXT PRIMARY KEY,
    year INTEGER NOT NULL,
    match_date DATE,
    team1 TEXT, team2 TEXT, winner TEXT,
    team1_score TEXT, team2_score TEXT, margin TEXT,
    ground TEXT, host_country TEXT
);

CREATE TABLE IF NOT EXISTS champions_trophy_matches (
    match_id TEXT PRIMARY KEY,
    year INTEGER NOT NULL,
    match_date DATE,
    team1 TEXT, team2 TEXT, toss TEXT, winner TEXT, margin TEXT,
    player_of_match TEXT, ground TEXT
);

CREATE TABLE IF NOT EXISTS wtc_matches (
    match_id TEXT PRIMARY KEY,
    cycle TEXT NOT NULL,
    match_no INTEGER,
    series TEXT,
    match_date DATE,
    ground TEXT, host_country TEXT,
    team1 TEXT, team2 TEXT,
    result_type TEXT, winner TEXT, result_summary TEXT
);

CREATE TABLE IF NOT EXISTS wtc_points_tables (
    cycle TEXT NOT NULL, team TEXT NOT NULL,
    matches INTEGER, won INTEGER, lost INTEGER, tied INTEGER, draw INTEGER,
    points NUMERIC, pct NUMERIC, final_position INTEGER,
    PRIMARY KEY (cycle, team)
);

CREATE TABLE IF NOT EXISTS odi_wc_standings (
    year INTEGER NOT NULL, stage TEXT NOT NULL, team TEXT NOT NULL,
    m INTEGER, w INTEGER, l INTEGER, t INTEGER, n_r INTEGER,
    pt NUMERIC, nrr NUMERIC, "for" TEXT, against TEXT,
    PRIMARY KEY (year, stage, team)
);

CREATE TABLE IF NOT EXISTS t20_wc_players (team TEXT, year INTEGER, player_name TEXT);
CREATE TABLE IF NOT EXISTS champions_trophy_players (team TEXT, year INTEGER, player_name TEXT);
CREATE TABLE IF NOT EXISTS wtc_records (cycle TEXT, category TEXT, rank INTEGER, player_team TEXT, detail TEXT, value TEXT);
CREATE TABLE IF NOT EXISTS wtc_venues (cycle TEXT, ground TEXT, matches_hosted INTEGER, country TEXT);
