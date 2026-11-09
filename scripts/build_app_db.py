"""Build data/app.db, the stats app's read-only copy of the database.

Usage: python scripts/build_app_db.py

The copy is built as data/app.db.tmp and replaces data/app.db only if
its integrity and foreign-key checks pass. Run it after each weekly
build_features.py.
"""
import _bootstrap  # noqa: F401

from scorecaster.config import Settings
from scorecaster.db.app_copy import AppDatabaseBuilder, AppDatabaseError


def main() -> None:
    """Build the app database and print rows per table and its size."""
    settings = Settings.from_env()
    target = settings.app_db_path
    builder = AppDatabaseBuilder(settings.db_path, target)
    try:
        counts = builder.build()
    except AppDatabaseError as error:
        raise SystemExit(
            f"{target} not replaced; the copy failed its checks:\n{error}"
        )
    for table, rows in counts.items():
        print(f"{table}: {rows:,} rows")
    print(f"{target}: {target.stat().st_size / 1_000_000:,.0f} MB")


if __name__ == "__main__":
    main()
