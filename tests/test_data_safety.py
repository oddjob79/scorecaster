"""Guarantees that protect stored data, and the tripwires against misuse."""
import pytest
import requests

import create_db
import load_data
from scorecaster.config import FeatureConfig
from scorecaster.db import Database, Download
from scorecaster.features.builder import FeatureBuilder
from scorecaster.features.calculators import FeatureCalculator
from scorecaster.features.pyramid import PyramidElo
from scorecaster.ingest.download import DownloadCache
from scorecaster.ingest.fdcuk import CsvLoader
from scorecaster.ingest.fdcuk.files import CsvFile
from scorecaster.ingest.fdcuk.fixtures import FixturesLoader
from tests.conftest import (
    LEAGUES_BY_CODE,
    read_fixture,
    rows,
    scalar,
    season_file,
)

UNSCORED_ROW = (
    "E0,21/09/2024,15:00,Ashford,Bexley,,,,,,,,,,,,,,,,,,,"
    ",,,,,,,,,,,,,\n"
)


@pytest.mark.parametrize(
    "current_season, status", [(2026, "void"), (2024, "scheduled")]
)
def test_unscored_matches_are_void_unless_the_season_is_current(
    db, current_season, status
):
    body = read_fixture("mini_E0.csv") + UNSCORED_ROW.encode()
    CsvLoader(db, current_season).load(season_file("E0", 2024), body)
    assert scalar(
        db, "SELECT status FROM matches WHERE match_date = '2024-09-21'"
    ) == status


def test_extra_league_files_load_every_season(db):
    bra = LEAGUES_BY_CODE["BRA"]
    CsvLoader(db, 2026).load(
        CsvFile(bra, None, "test://BRA"), read_fixture("mini_BRA.csv")
    )
    assert rows(db, "SELECT label FROM seasons ORDER BY label") == [
        ("2023",), ("2024",)
    ]
    assert scalar(db, "SELECT COUNT(*) FROM odds") == 18


def test_fixtures_never_overwrite_a_finished_match(loaded_db):
    FixturesLoader(loaded_db).load(
        read_fixture("mini_fixtures.csv"), "fixtures"
    )
    finished = rows(
        loaded_db,
        "SELECT m.status, m.ft_home, m.ft_away FROM matches m "
        "JOIN teams h ON h.id = m.home_team_id "
        "WHERE h.name = 'Crawley' AND m.match_date = '2024-09-14'",
    )
    assert finished == [("finished", 0, 1)]
    new = rows(
        loaded_db,
        "SELECT m.status, COUNT(o.id) FROM matches m "
        "LEFT JOIN odds o ON o.match_id = m.id "
        "WHERE m.match_date = '2024-09-21' GROUP BY m.id",
    )
    assert new == [("scheduled", 5)]


class FakeResponse:
    """A response with a fixed body, or a 404 for URLs ending 'missing'."""

    def __init__(self, url: str, call: int) -> None:
        self.status_code = 404 if url.endswith("missing") else 200
        self.content = f"{url}#{call}".encode()

    def raise_for_status(self) -> None:
        if self.status_code != 200:
            raise requests.HTTPError(response=self)


class FakeSession:
    """Record each requested URL instead of using the network."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    def get(self, url: str, timeout: float) -> FakeResponse:
        self.calls.append(url)
        return FakeResponse(url, len(self.calls))


class NoWait:
    def wait(self) -> None:
        pass


def test_download_cache_fetches_once_and_refresh_fetches_again(db):
    session = FakeSession()
    cache = DownloadCache(db, limiter=NoWait(), session=session)
    assert cache.get("u/a") == b"u/a#1"
    assert cache.get("u/a") == b"u/a#1"
    assert cache.refresh("u/a") == b"u/a#2"
    assert cache.get("u/a") == b"u/a#2"
    assert session.calls == ["u/a", "u/a"]
    with db.session() as s:
        assert s.query(Download).count() == 1


class MissingCache:
    """A cache whose every fetch is a 404."""

    def get(self, url: str) -> bytes:
        raise requests.HTTPError(response=FakeResponse("missing", 0))

    refresh = get


def test_fetch_skips_a_missing_current_season_only():
    current = season_file("E0", 2026)
    past = season_file("E0", 2024)
    assert load_data.fetch(MissingCache(), current, False, 2026) is None
    with pytest.raises(requests.HTTPError):
        load_data.fetch(MissingCache(), past, False, 2026)


def test_schema_drift_is_reported_and_stops_create_db(db):
    with db.engine.begin() as connection:
        connection.exec_driver_sql("ALTER TABLE matches DROP COLUMN referee")
    assert db.schema_differences() == ["matches.referee: not in database"]
    with pytest.raises(SystemExit):
        create_db.check_schema(db)


def test_matching_schema_has_no_differences(db):
    assert db.schema_differences() == []


class WrongKeys(FeatureCalculator):
    def columns(self) -> list[str]:
        return ["declared"]

    def compute(self, ctx) -> dict:
        return {"something_else": 1}


def test_a_calculator_returning_wrong_keys_stops_the_build(loaded_db):
    builder = FeatureBuilder(
        loaded_db, FeatureConfig(), calculators=[WrongKeys()]
    )
    with pytest.raises(RuntimeError, match="WrongKeys"):
        builder.rebuild()


def test_elo_rejects_a_team_from_another_division():
    with pytest.raises(ValueError, match="isn't in division"):
        PyramidElo(FeatureConfig()).update(1, 10, 20, 1, 0)


def test_end_to_end_mini_season(featured_db: Database):
    assert scalar(
        featured_db, "SELECT COUNT(*) FROM team_match_features"
    ) == 24
    ashford_last = rows(
        featured_db,
        "SELECT f.league_position, f.season_phase, f.form_4_pts, "
        "f.market_win_prob "
        "FROM team_match_features f JOIN teams t ON t.id = f.team_id "
        "WHERE t.name = 'Ashford' AND f.match_date = '2024-09-14'",
    )
    position, phase, form_4, market_win = ashford_last[0]
    assert (position, phase, form_4) == (1, 5, 8)
    assert market_win == pytest.approx(
        (1 / 3.5) / (1 / 2.0 + 1 / 3.3 + 1 / 3.5)
    )
