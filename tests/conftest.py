"""Shared fixtures: in-memory databases and the small CSV files.

`mini_E0.csv` is a four-team Premier League season (2024/25), each team
playing the others home and away: 12 matches over six Saturdays, with
stats and Pinnacle, market-average and Asian handicap odds.
"""
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import create_db  # noqa: E402

from scorecaster.config import FeatureConfig  # noqa: E402
from scorecaster.db import Database  # noqa: E402
from scorecaster.features.builder import FeatureBuilder  # noqa: E402
from scorecaster.ingest.fdcuk import CsvLoader  # noqa: E402
from scorecaster.ingest.fdcuk.files import CsvFile  # noqa: E402
from scorecaster.leagues import LEAGUES  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures"
LEAGUES_BY_CODE = {league.code: league for league in LEAGUES}
PAST_SEASON_CURRENT = 2026  # loading 2024/25 as a finished season


def read_fixture(name: str) -> bytes:
    """Return a CSV fixture's raw bytes."""
    return (FIXTURES / name).read_bytes()


def season_file(code: str, season_start: int) -> CsvFile:
    """Return a per-season CsvFile for a league, with a dummy URL."""
    return CsvFile(
        LEAGUES_BY_CODE[code], season_start, f"test://{code}/{season_start}"
    )


@pytest.fixture
def db() -> Database:
    """Return an empty in-memory database with the league list synced."""
    database = Database("sqlite://")
    database.create_schema()
    create_db.sync_competitions(database, LEAGUES)
    return database


@pytest.fixture
def loaded_db(db: Database) -> Database:
    """Return the database with the mini Premier League season loaded."""
    loader = CsvLoader(db, PAST_SEASON_CURRENT)
    loader.load(season_file("E0", 2024), read_fixture("mini_E0.csv"))
    return db


@pytest.fixture
def featured_db(loaded_db: Database) -> Database:
    """Return the mini season with its feature table built."""
    FeatureBuilder(loaded_db, FeatureConfig()).rebuild()
    return loaded_db


def scalar(db: Database, sql: str):
    """Return the single value an SQL query selects."""
    with db.engine.connect() as connection:
        return connection.exec_driver_sql(sql).scalar()


def rows(db: Database, sql: str) -> list[tuple]:
    """Return every row an SQL query selects."""
    with db.engine.connect() as connection:
        return [tuple(row) for row in connection.exec_driver_sql(sql)]
