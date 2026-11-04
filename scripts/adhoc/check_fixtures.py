"""Compare the stored scheduled fixtures with the cached fixtures files.

For each fixtures file, count its rows and the non-empty prices of the
stored bookmakers, then count the scheduled matches and their pre-match
odds in the database. The database is opened read-only.

    python scripts/adhoc/check_fixtures.py
"""
import io
import sqlite3

import pandas as pd

import _bootstrap  # noqa: F401

from scorecaster.config import Settings
from scorecaster.ingest.fdcuk.columns import OddsColumn
from scorecaster.ingest.fdcuk.files import FIXTURES_URLS
from scorecaster.ingest.fdcuk.reader import decode_csv

STORED_SCHEDULED = """
    SELECT m.match_date, h.name AS home, a.name AS away,
           COUNT(o.id) AS odds_stored
    FROM matches m
    JOIN teams h ON h.id = m.home_team_id
    JOIN teams a ON a.id = m.away_team_id
    LEFT JOIN odds o ON o.match_id = m.id AND o.timing = 'pre_match'
    WHERE m.status = 'scheduled'
    GROUP BY m.id
"""


def main() -> None:
    """Print file and database counts side by side, then any differences."""
    with sqlite3.connect(_read_only_uri(), uri=True) as connection:
        stored_df = pd.read_sql_query(STORED_SCHEDULED, connection)
        for url in FIXTURES_URLS:
            body = _stored_body(connection, url)
            compare(url.rsplit("/", 1)[-1], _file_counts(body), stored_df)


def compare(
    label: str, file_df: pd.DataFrame, stored_df: pd.DataFrame
) -> None:
    """Match file rows to stored fixtures and report any difference."""
    merged_df = file_df.merge(stored_df, on=["home", "away"], how="left")
    missing = merged_df["odds_stored"].isna()
    wrong_odds = ~missing & (
        merged_df["odds_file"] != merged_df["odds_stored"]
    )
    print(
        f"{label}: {len(file_df)} fixtures, "
        f"{int(file_df['odds_file'].sum())} prices in the file; "
        f"{int(merged_df['odds_stored'].sum())} stored"
    )
    for _, row in merged_df[missing | wrong_odds].iterrows():
        print(
            f"  differs: {row['home']} v {row['away']} "
            f"file {row['odds_file']} stored {row['odds_stored']}"
        )


def _file_counts(body: bytes) -> pd.DataFrame:
    """Return each fixture's teams and its number of stored-source prices."""
    file_df = pd.read_csv(io.StringIO(decode_csv(body)), dtype=str)
    file_df = file_df.rename(columns={"Home": "HomeTeam", "Away": "AwayTeam"})
    price_columns = [
        name for name in file_df.columns if OddsColumn.parse(name)
    ]
    return pd.DataFrame({
        "home": file_df["HomeTeam"].str.strip(),
        "away": file_df["AwayTeam"].str.strip(),
        "odds_file": file_df[price_columns].notna().sum(axis=1),
    })


def _stored_body(connection: sqlite3.Connection, url: str) -> bytes:
    """Return the cached body for `url`."""
    row = connection.execute(
        "SELECT body FROM downloads WHERE url = ?", (url,)
    ).fetchone()
    return row[0]


def _read_only_uri() -> str:
    """Return a SQLite URI that opens the database read-only."""
    return f"file:{Settings.from_env().db_path}?mode=ro"


if __name__ == "__main__":
    main()
