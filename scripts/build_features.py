"""Build or update the pre-match team_match_features table from stored matches."""
import argparse

import _bootstrap  # noqa: F401

from percy.config import Settings
from percy.db import Database
from percy.features.builder import FeatureBuilder


def main() -> None:
    """Incrementally compute features; --rebuild recreates the derived table from scratch."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rebuild", action="store_true", help="drop and rebuild the derived feature table")
    args = parser.parse_args()
    settings = Settings.from_env()
    db = Database.for_path(settings.db_path)
    stats = FeatureBuilder(db, settings.features).build(rebuild=args.rebuild)
    print(f"done: {stats}")


if __name__ == "__main__":
    main()
