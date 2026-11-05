"""Download football-data.co.uk files into the downloads table.

Each name is a path on the site, e.g. ``fixtures.csv`` or
``mmz4281/2425/E0.csv``. Files already stored are left alone unless
--refresh is given.

    python scripts/adhoc/fetch_files.py fixtures.csv new_league_fixtures.csv
"""
import argparse

import _bootstrap  # noqa: F401

from scorecaster.config import Settings
from scorecaster.db import Database
from scorecaster.ingest.download import DownloadCache
from scorecaster.ingest.fdcuk.files import BASE_URL


def main() -> None:
    """Fetch each named file, from the database if stored, else the site."""
    args = parse_args()
    cache = DownloadCache(Database.for_path(Settings.from_env().db_path))
    for name in args.names:
        url = f"{BASE_URL}/{name}"
        if args.refresh:
            cache.refresh(url)
        else:
            cache.get(url)


def parse_args() -> argparse.Namespace:
    """Read the file names and the --refresh option."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("names", nargs="+", help="paths on the site")
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="download again even if already stored",
    )
    return parser.parse_args()


if __name__ == "__main__":
    main()
