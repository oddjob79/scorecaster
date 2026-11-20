"""The stats app's database: what the copy holds and how it is replaced."""
import pytest

from scorecaster.db import Database
from scorecaster.db.app_copy import (
    APP_COUNTRIES,
    AppDatabaseBuilder,
    AppDatabaseError,
)
from tests.conftest import rows, scalar


def open_db(path) -> Database:
    """Return a Database on an SQLite file."""
    return Database(f"sqlite:///{path}")


def test_the_copy_holds_the_app_competitions(app_db_path):
    app_db = open_db(app_db_path)
    countries = rows(app_db, "SELECT DISTINCT country FROM competitions")
    assert {country for (country,) in countries} == set(APP_COUNTRIES)
    assert scalar(app_db, "SELECT COUNT(*) FROM competitions") == 20


def test_the_copy_holds_the_mini_season(app_db_path):
    app_db = open_db(app_db_path)
    assert rows(app_db, "SELECT label FROM seasons") == [("2024/25",)]
    assert scalar(app_db, "SELECT COUNT(*) FROM matches") == 12
    assert scalar(app_db, "SELECT COUNT(*) FROM teams") == 4
    assert scalar(app_db, "SELECT COUNT(*) FROM team_match_features") == 24


def test_the_copy_keeps_only_market_average_odds(
    source_db_path, app_db_path
):
    source_db = open_db(source_db_path)
    app_db = open_db(app_db_path)
    assert rows(app_db, "SELECT DISTINCT bookmaker FROM odds") == [
        ("market_avg",)
    ]
    assert scalar(app_db, "SELECT COUNT(*) FROM odds") == scalar(
        source_db,
        "SELECT COUNT(*) FROM odds WHERE bookmaker = 'market_avg'",
    )


def test_a_successful_build_leaves_no_staging_file(app_db_path):
    assert not app_db_path.with_name("app.db.tmp").exists()


def test_a_failed_check_keeps_the_existing_copy(
    source_db_path, monkeypatch
):
    target = source_db_path.with_name("app.db")
    target.write_text("previous copy")
    monkeypatch.setattr(
        AppDatabaseBuilder,
        "_problems",
        lambda self, connection: ["integrity: broken page"],
    )
    with pytest.raises(AppDatabaseError, match="integrity: broken page"):
        AppDatabaseBuilder(source_db_path, target).build()
    assert target.read_text() == "previous copy"
