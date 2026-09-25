"""Create the SQLite database and raw tables. Existing tables and data are never touched."""
import argparse
from pathlib import Path

import _bootstrap  # noqa: F401

from percy.config import Settings
from percy.db import Database


def main() -> None:
    """Create any missing raw tables in the configured database."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", help="database path (default from settings)")
    args = parser.parse_args()
    settings = Settings.from_env()
    path = settings.db_path if args.db is None else Path(args.db)
    created = Database.for_path(path).create_schema()
    print(f"{path}: created {created}" if created else f"{path}: all tables already exist, nothing changed")


if __name__ == "__main__":
    main()
