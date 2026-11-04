"""Export the modelling dataset to CSV.

By default: one row per finished match. --upcoming exports fixtures
instead, and --per-team gives one row per team per match.
"""
import argparse

import _bootstrap  # noqa: F401

from scorecaster.analysis.dataset import DatasetLoader
from scorecaster.config import Settings
from scorecaster.db import Database


def main() -> None:
    """Write the selected rows to a CSV file and report its size."""
    args = parse_args()
    loader = DatasetLoader(Database.for_path(Settings.from_env().db_path))
    finished = not args.upcoming
    if args.per_team:
        dataset_df = loader.team_matches(finished)
    else:
        dataset_df = loader.matches(finished)
    dataset_df.to_csv(args.output, index=False)
    rows, columns = dataset_df.shape
    print(f"wrote {rows} rows x {columns} columns to {args.output}")


def parse_args() -> argparse.Namespace:
    """Read the output path and options."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", help="CSV path")
    parser.add_argument(
        "--upcoming",
        action="store_true",
        help="export upcoming fixtures instead",
    )
    parser.add_argument(
        "--per-team",
        action="store_true",
        help="one row per team per match",
    )
    return parser.parse_args()


if __name__ == "__main__":
    main()
