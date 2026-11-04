"""Build or update the pre-match team_match_features table.

By default only new matches are added and scheduled matches refreshed.
--rebuild drops the table and computes every row again, which is needed
whenever the feature columns change.
"""
import argparse

import _bootstrap  # noqa: F401

from scorecaster.config import Settings
from scorecaster.db import Database
from scorecaster.features.builder import FeatureBuilder


def main() -> None:
    """Build the feature table and print the counts."""
    args = parse_args()
    settings = Settings.from_env()
    builder = FeatureBuilder(
        Database.for_path(settings.db_path), settings.features
    )
    stats = builder.rebuild() if args.rebuild else builder.build()
    print(f"done: {stats}")


def parse_args() -> argparse.Namespace:
    """Read the command-line options."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="drop and rebuild the derived feature table",
    )
    return parser.parse_args()


if __name__ == "__main__":
    main()
