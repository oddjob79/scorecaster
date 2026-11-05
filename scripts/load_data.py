"""Download football-data.co.uk CSVs and load them into the database.

Each file is downloaded once and kept in the database, so re-runs read
from there. Results, stats and odds go into the seasons, teams, matches
and odds tables. An unfiltered run then loads the fixtures files, which
add upcoming matches as 'scheduled' with their pre-match odds.
"""
import argparse
import logging

import requests

import _bootstrap  # noqa: F401

from scorecaster.config import Settings
from scorecaster.db import Database
from scorecaster.ingest.download import DownloadCache
from scorecaster.ingest.fdcuk import CsvLoader
from scorecaster.ingest.fdcuk.files import (
    FIXTURES_URLS,
    CsvFile,
    list_csv_files,
)
from scorecaster.ingest.fdcuk.fixtures import FixturesLoader
from scorecaster.leagues import LEAGUES, current_season_start

log = logging.getLogger("load_data")


def main() -> None:
    """Load the selected season files, then the fixtures, logging totals.

    Fixtures load on an unfiltered run, or alone with --fixtures-only.
    """
    args = parse_args()
    db = Database.for_path(Settings.from_env().db_path)
    cache = DownloadCache(db)
    if not args.fixtures_only:
        load_season_files(db, cache, args.league, args.season, args.refresh)
    if args.fixtures_only or not (args.league or args.season):
        written = load_fixtures(cache, FixturesLoader(db), args.refresh)
        log.info("%d fixtures", written)


def load_season_files(
    db: Database,
    cache: DownloadCache,
    leagues: list[str] | None,
    seasons: list[int] | None,
    refresh: bool,
) -> None:
    """Fetch and load the selected league-season and extra-league files."""
    current_season = current_season_start()
    loader = CsvLoader(db, current_season)
    files = select_files(leagues, seasons, current_season)
    total = 0
    for csv_file in files:
        body = fetch(cache, csv_file, refresh, current_season)
        if body is not None:
            total += loader.load(csv_file, body)
    log.info("%d files, %d matches", len(files), total)


def parse_args() -> argparse.Namespace:
    """Read the command-line options."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="re-download files that can still change",
    )
    parser.add_argument(
        "--league",
        action="append",
        help="league code to load, e.g. E0 (repeatable)",
    )
    parser.add_argument(
        "--season",
        action="append",
        type=int,
        help="season start year, e.g. 2024 (repeatable); "
        "skips the all-seasons extra-league files",
    )
    parser.add_argument(
        "--fixtures-only",
        action="store_true",
        help="load just the two fixtures files",
    )
    return parser.parse_args()


def select_files(
    leagues: list[str] | None,
    seasons: list[int] | None,
    current_season: int,
) -> list[CsvFile]:
    """Return the configured files, narrowed to the given leagues and seasons.

    No leagues or seasons means all of them. Giving seasons leaves out the
    all-seasons files, since they can't be narrowed to one season.
    """
    files = list_csv_files(LEAGUES, current_season)
    if leagues:
        files = [f for f in files if f.league.code in leagues]
    if seasons:
        files = [f for f in files if f.season_start in seasons]
    return files


def fetch(
    cache: DownloadCache,
    csv_file: CsvFile,
    refresh: bool,
    current_season: int,
) -> bytes | None:
    """Return a file's body, or None if the current season isn't out yet.

    The site publishes a new season's file a few weeks into the season, so
    a 404 for the season in progress is expected. Any other error stops
    the run.
    """
    try:
        if refresh and csv_file.is_live(current_season):
            return cache.refresh(csv_file.url)
        return cache.get(csv_file.url)
    except requests.HTTPError as error:
        is_missing = error.response.status_code == 404
        if is_missing and csv_file.season_start == current_season:
            log.info("not published yet, skipped: %s", csv_file.url)
            return None
        raise


def load_fixtures(
    cache: DownloadCache, loader: FixturesLoader, refresh: bool
) -> int:
    """Load both fixtures files, re-downloading them first if refreshing.

    Returns the number of fixtures written.
    """
    written = 0
    for url in FIXTURES_URLS:
        body = cache.refresh(url) if refresh else cache.get(url)
        written += loader.load(body, label=url.rsplit("/", 1)[-1])
    return written


if __name__ == "__main__":
    main()
