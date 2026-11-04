"""Download football-data.co.uk CSVs (once, cached in the database) and load them into seasons, teams, matches and odds."""
import argparse
import logging

import requests

import _bootstrap  # noqa: F401

from scorecaster.config import LEAGUES, Settings, current_season_start
from scorecaster.db import Database
from scorecaster.ingest.download import DownloadCache, list_csv_files
from scorecaster.ingest.fdcuk import CsvLoader

log = logging.getLogger("load_data")


def main() -> None:
    """Fetch and load every configured file, optionally narrowed by league and season (--season skips extra leagues)."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true", help="re-download files that can still change")
    parser.add_argument("--league", action="append", help="league code to load, e.g. E0 (repeatable)")
    parser.add_argument("--season", action="append", type=int,
                        help="season start year, e.g. 2024 (repeatable); excludes all-seasons files")
    args = parser.parse_args()

    db = Database.for_path(Settings.from_env().db_path)
    cache = DownloadCache(db)
    current = current_season_start()
    loader = CsvLoader(db, current)
    files = [f for f in list_csv_files(LEAGUES, current)
             if (not args.league or f.league.code in args.league)
             and (not args.season or f.season_start in args.season)]

    total = 0
    for csv_file in files:
        try:
            body = cache.get(csv_file.url, refresh=args.refresh and csv_file.is_live(current))
        except requests.HTTPError as exc:
            if exc.response.status_code == 404 and csv_file.season_start == current:
                log.info("not published yet, skipped: %s", csv_file.url)
                continue
            raise
        total += loader.load(csv_file, body)
    log.info("%d files, %d matches", len(files), total)


if __name__ == "__main__":
    main()
