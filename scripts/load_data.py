"""Load a competition's seasons from football-data.org into the local database (cached, re-runnable)."""
import argparse
from datetime import date

import _bootstrap  # noqa: F401

from percy.api import CachedJsonClient, FootballDataOrgProvider
from percy.config import Settings
from percy.db import Database
from percy.ingest.loader import HistoricalLoader


def default_seasons(count: int = 5) -> list[int]:
    """Start years of the current season and the previous `count - 1`."""
    today = date.today()
    current = today.year if today.month >= 7 else today.year - 1
    return list(range(current - count + 1, current + 1))


def main() -> None:
    """Fetch seasons (served from the response cache where possible) and store them."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--competition", help="competition code, e.g. PL")
    parser.add_argument("--seasons", type=int, nargs="+", help="season start years, e.g. 2021 2022")
    parser.add_argument("--refresh", action="store_true", help="re-request seasons that are not yet complete")
    args = parser.parse_args()

    settings = Settings.from_env()
    if not settings.football_data_key:
        raise SystemExit("FOOTBALL_DATA_KEY is not set")
    db = Database.for_path(settings.db_path)
    db.create_schema()
    provider = FootballDataOrgProvider.build(settings.football_data_key, settings.football_data_base_url,
                                             settings.requests_per_minute, cache=lambda c: CachedJsonClient(c, db))
    stats = HistoricalLoader(provider, db).load(args.competition or settings.competition_code,
                                                args.seasons or default_seasons(), refresh_current=args.refresh)
    print(f"done: {stats}")


if __name__ == "__main__":
    main()
