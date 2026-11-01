"""Export the modelling dataset (one row per match) to CSV."""
import argparse

import _bootstrap  # noqa: F401

from scorecaster.analysis.dataset import DatasetLoader
from scorecaster.config import Settings
from scorecaster.db import Database


def main() -> None:
    """Write finished (default) or upcoming matches with features to a CSV file."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", help="CSV path")
    parser.add_argument("--upcoming", action="store_true", help="export upcoming fixtures instead")
    parser.add_argument("--per-team", action="store_true", help="one row per team per match")
    args = parser.parse_args()
    loader = DatasetLoader(Database.for_path(Settings.from_env().db_path))
    finished = not args.upcoming
    frame = loader.team_matches(finished) if args.per_team else loader.matches(finished)
    frame.to_csv(args.output, index=False)
    print(f"wrote {len(frame)} rows x {frame.shape[1]} columns to {args.output}")


if __name__ == "__main__":
    main()
