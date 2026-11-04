"""Build features for a few leagues in a throwaway in-memory database.

Copies the chosen leagues' matches and their market-average pre-match
odds (and every competition and team) from the real database, opened
read-only, into memory, runs the feature
builder there, then reports timing, row counts, columns that are mostly
empty, and one team's rows. Nothing is written to the real database.

    python scripts/adhoc/sample_feature_build.py --league E0 --league E1
"""
import argparse
import sqlite3
import time

import pandas as pd

import _bootstrap  # noqa: F401

from scorecaster.config import FeatureConfig, Settings
from scorecaster.db import (
    Competition,
    Database,
    Match,
    Odds,
    Season,
    Team,
)
from scorecaster.features.builder import FeatureBuilder
from scorecaster.features.schema import TABLE_NAME

ENGLAND = ["E0", "E1", "E2", "E3", "EC"]
SHOWN_COLUMNS = [
    "match_date", "is_home", "goals_for", "goals_against",
    "season_phase", "league_position", "position_band",
    "elo", "elo_expected", "form_6_pts",
    "market_win_prob", "stats_6_shots_for_pg",
]


def main() -> None:
    """Copy, build, and print the checks."""
    args = parse_args()
    memory = Database("sqlite://")
    memory.create_schema()
    copied = copy_leagues(memory, args.league or ENGLAND)
    print(f"copied {copied} matches for {', '.join(args.league or ENGLAND)}")

    started = time.perf_counter()
    stats = FeatureBuilder(memory, FeatureConfig()).rebuild()
    elapsed = time.perf_counter() - started
    print(f"built in {elapsed:.1f}s ({1000 * elapsed / copied:.2f} ms per "
          f"match): {stats}")

    features_df = pd.read_sql_table(TABLE_NAME, memory.engine)
    print_empty_columns(features_df)
    print_team(features_df, memory, args.team)


def parse_args() -> argparse.Namespace:
    """Read the leagues to copy and the team to show."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--league",
        action="append",
        help="league code to copy (repeatable); default: English pyramid",
    )
    parser.add_argument(
        "--team", default="Burnley", help="team whose rows to print"
    )
    return parser.parse_args()


def copy_leagues(memory: Database, codes: list[str]) -> int:
    """Copy everything a feature build reads for the chosen leagues.

    All competitions and teams; the leagues' seasons and matches; and
    those matches' market-average pre-match odds.
    """
    source_uri = f"file:{Settings.from_env().db_path}?mode=ro"
    marks = ", ".join("?" for _ in codes)
    league_filter = (
        f"competition_id IN (SELECT id FROM competitions "
        f"WHERE code IN ({marks}))"
    )
    with sqlite3.connect(source_uri, uri=True) as source:
        tables = {
            Competition: pd.read_sql_query(
                "SELECT * FROM competitions", source
            ),
            Team: pd.read_sql_query("SELECT * FROM teams", source),
            Season: pd.read_sql_query(
                f"SELECT * FROM seasons WHERE {league_filter}",
                source,
                params=codes,
            ),
            Match: pd.read_sql_query(
                f"SELECT * FROM matches WHERE {league_filter}",
                source,
                params=codes,
                parse_dates=["match_date"],
            ),
            Odds: pd.read_sql_query(
                "SELECT o.* FROM odds o JOIN matches m ON m.id = o.match_id "
                f"WHERE m.{league_filter} AND o.bookmaker = 'market_avg' "
                "AND o.timing = 'pre_match'",
                source,
                params=codes,
            ),
        }
    matches_df = tables[Match]
    matches_df["match_date"] = matches_df["match_date"].dt.date
    matches_df["kickoff_time"] = None
    with memory.engine.begin() as connection:
        for model, table_df in tables.items():
            rows = table_df.astype(object).where(table_df.notna(), None)
            connection.execute(
                model.__table__.insert(), rows.to_dict("records")
            )
    return len(matches_df)


def print_empty_columns(features_df: pd.DataFrame) -> None:
    """Print feature columns that are empty in more than half the rows."""
    empty_share = features_df.isna().mean().sort_values(ascending=False)
    mostly_empty = empty_share[empty_share > 0.5]
    print(f"{len(features_df)} rows x {features_df.shape[1]} columns; "
          f"{len(mostly_empty)} columns more than half empty:")
    for column, share in mostly_empty.items():
        print(f"  {column}: {share:.0%} empty")


def print_team(
    features_df: pd.DataFrame, memory: Database, team_name: str
) -> None:
    """Print one team's last 12 rows, to eyeball the values."""
    teams_df = pd.read_sql_table("teams", memory.engine)
    team_ids = teams_df.loc[teams_df["name"] == team_name, "id"]
    if team_ids.empty:
        print(f"no team called {team_name}")
        return
    team_df = features_df[features_df["team_id"] == team_ids.iloc[0]]
    print(f"\n{team_name}, last 12 rows:")
    with pd.option_context("display.width", 200):
        print(team_df.sort_values("match_date")[SHOWN_COLUMNS]
              .tail(12).to_string(index=False))


if __name__ == "__main__":
    main()
