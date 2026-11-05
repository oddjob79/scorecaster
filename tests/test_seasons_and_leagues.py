"""Season labels, the season in progress, and the league config."""
import re
from datetime import date

import pytest
from pydantic import ValidationError

from scorecaster.ingest.fdcuk.files import list_csv_files, season_dir
from scorecaster.ingest.fdcuk.fixtures import season_for
from scorecaster.ingest.fdcuk.seasons import SeasonSpan
from scorecaster.leagues import LEAGUES, LeagueConfig, current_season_start

LEAGUES_BY_CODE = {league.code: league for league in LEAGUES}


def test_season_span_starting_labels_august_to_may_seasons():
    assert SeasonSpan.starting(2024) == SeasonSpan("2024/25", 2024, 2025)
    assert SeasonSpan.starting(2099) == SeasonSpan("2099/00", 2099, 2100)


def test_season_span_parse_reads_both_label_styles():
    assert SeasonSpan.parse("2012/2013") == SeasonSpan("2012/13", 2012, 2013)
    assert SeasonSpan.parse(" 2024 ") == SeasonSpan("2024", 2024, 2024)
    assert SeasonSpan.parse("2024").is_calendar_year
    assert not SeasonSpan.parse("2012/2013").is_calendar_year


@pytest.mark.parametrize(
    "day, start",
    [(date(2026, 7, 1), 2026), (date(2026, 6, 30), 2025),
     (date(2027, 3, 1), 2026)],
)
def test_current_season_start_turns_over_in_july(day, start):
    assert current_season_start(day) == start


def test_season_for_uses_each_league_calendar():
    day = date(2027, 3, 1)
    assert season_for(LEAGUES_BY_CODE["E0"], day).label == "2026/27"
    assert season_for(LEAGUES_BY_CODE["BRA"], day).label == "2027"


def test_season_dir_matches_the_site_folders():
    assert season_dir(2024) == "2425"
    assert season_dir(2005) == "0506"


@pytest.mark.parametrize(
    "fields",
    [
        {"tier": 0, "file_style": "season", "first_season": 2005},
        {"tier": 1, "file_style": "season", "first_season": None},
        {"tier": 1, "file_style": "season", "first_season": 2999},
        {"tier": 1, "file_style": "weekly"},
    ],
)
def test_league_config_rejects_invalid_leagues(fields):
    with pytest.raises(ValidationError):
        LeagueConfig(code="X1", country="Nowhere", name="Test", **fields)


def test_every_configured_league_is_unique_and_has_valid_urls():
    codes = [league.code for league in LEAGUES]
    assert len(codes) == len(set(codes))
    url_pattern = re.compile(
        r"^https://www\.football-data\.co\.uk/"
        r"(mmz4281/\d{4}/[A-Z0-9]+|new/[A-Z]+)\.csv$"
    )
    for csv_file in list_csv_files(LEAGUES, 2026):
        assert url_pattern.match(csv_file.url), csv_file.url
