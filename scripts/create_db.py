"""Create the SQLite database and raw tables, then sync competitions from the league config. Existing data is never deleted."""
import argparse
from pathlib import Path

import _bootstrap  # noqa: F401

from scorecaster.config import LEAGUES, Settings
from scorecaster.db import Database


def main() -> None:
    """Create any missing raw tables and upsert the configured leagues into competitions."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", help="database path (default from settings)")
    args = parser.parse_args()
    settings = Settings.from_env()
    path = settings.db_path if args.db is None else Path(args.db)
    db = Database.for_path(path)
    created = db.create_schema()
    print(f"{path}: created {created}" if created else f"{path}: all tables already exist, nothing changed")
    print(f"{path}: {db.upsert_competitions(LEAGUES)} competitions synced from config")


if __name__ == "__main__":
    main()
