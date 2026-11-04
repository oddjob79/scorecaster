"""Create the SQLite database and its tables, then sync the league list.

Missing tables are created and existing ones are left alone, so no data
is ever deleted. Competitions are inserted or updated from the config.
"""
import argparse
from pathlib import Path

import _bootstrap  # noqa: F401

from scorecaster.config import Settings
from scorecaster.db import Competition, Database, upsert
from scorecaster.leagues import LEAGUES, LeagueConfig


def main() -> None:
    """Create missing tables and sync competitions, reporting both."""
    path = database_path(parse_args().db)
    db = Database.for_path(path)
    created = db.create_schema()
    if created:
        print(f"{path}: created {created}")
    else:
        print(f"{path}: all tables already exist, nothing changed")
    synced = sync_competitions(db, LEAGUES)
    print(f"{path}: {synced} competitions synced from config")


def parse_args() -> argparse.Namespace:
    """Read the command-line options."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", help="database path (default from settings)")
    return parser.parse_args()


def database_path(override: str | None) -> Path:
    """Return the --db path if given, otherwise the configured one."""
    if override is not None:
        return Path(override)
    return Settings.from_env().db_path


def sync_competitions(
    db: Database, leagues: tuple[LeagueConfig, ...]
) -> int:
    """Insert or update one competitions row per league, keyed by code.

    Returns the number of leagues synced.
    """
    rows = [
        league.model_dump(include={"code", "country", "name", "tier"})
        for league in leagues
    ]
    with db.session() as session:
        upsert(session, Competition.__table__, rows, ["code"])
    return len(rows)


if __name__ == "__main__":
    main()
