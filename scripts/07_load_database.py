"""
Optional: loads every processed CSV into the matching Postgres table defined
in database/schema.sql. Not required for normal use - the API reads the CSVs
in data/processed/ directly. Only useful if you've stood up Postgres and want
to query the data with SQL instead.

Usage:
    export DATABASE_URL=postgresql://user:pass@host:5432/dbname
    python scripts/load_database.py
"""
import os
import sys
import pandas as pd

try:
    from sqlalchemy import create_engine
except ImportError:
    sys.exit("Install sqlalchemy + psycopg2-binary first: pip install sqlalchemy psycopg2-binary")

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed"

TABLE_MAP = {
    "tournament_editions.csv": "tournament_editions",
    "odi_wc_matches.csv": "odi_wc_matches",
    "odi_wc_standings.csv": "odi_wc_standings",
    "t20_wc_matches.csv": "t20_wc_matches",
    "t20_wc_players.csv": "t20_wc_players",
    "champions_trophy_matches.csv": "champions_trophy_matches",
    "champions_trophy_players.csv": "champions_trophy_players",
    "wtc_matches.csv": "wtc_matches",
    "wtc_points_tables.csv": "wtc_points_tables",
    "wtc_records.csv": "wtc_records",
    "wtc_venues.csv": "wtc_venues",
}


def main():
    url = os.environ.get("DATABASE_URL")
    if not url:
        sys.exit("Set DATABASE_URL first, e.g. postgresql://user:pass@localhost:5432/icc")

    schema_sql = (ROOT / "database" / "schema.sql").read_text()
    engine = create_engine(url)
    with engine.begin() as conn:
        for stmt in schema_sql.split(";"):
            if stmt.strip():
                conn.exec_driver_sql(stmt)

        for csv_name, table in TABLE_MAP.items():
            path = DATA / csv_name
            if not path.exists():
                print(f"skip (missing): {csv_name}")
                continue
            df = pd.read_csv(path)
            df.to_sql(table, conn, if_exists="append", index=False)
            print(f"loaded {len(df):>5} rows -> {table}")


if __name__ == "__main__":
    main()
