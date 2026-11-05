"""Decisions: proportional position bands, season phase, unplayed status.

- Bands are fifths of each league's table, `ceil(position × 5 / size)`
  (chunk 09, replacing fixed 20-team bands).
- Season phase is the fifth of a team's season a game falls in, capped
  at 5 (chunk 09, analysed in 09a).
- An unscored match is 'scheduled' in the season in progress and 'void'
  in any earlier one (chunk 05; calendar-year leagues by year, chunk 07).
"""
import pytest

from scorecaster.features.calculators import season_phase
from scorecaster.features.table import band_of
from scorecaster.ingest.fdcuk import CsvLoader
from scorecaster.ingest.fdcuk.seasons import SeasonSpan


@pytest.mark.parametrize(
    "size, positions_by_band",
    [
        (20, {1: [1, 4], 2: [5, 8], 5: [17, 20]}),
        (24, {1: [1, 4], 2: [5, 9], 5: [20, 24]}),
        (18, {1: [1, 3], 2: [4, 7], 5: [15, 18]}),
    ],
)
def test_bands_are_fifths_of_the_table(size, positions_by_band):
    for band, positions in positions_by_band.items():
        for position in positions:
            assert band_of(position, size, 5) == band


def test_band_is_empty_without_a_position():
    assert band_of(None, 20, 5) is None


@pytest.mark.parametrize(
    "game, season_games, phase",
    [(1, 38, 1), (7, 38, 1), (8, 38, 2), (38, 38, 5), (41, 38, 5),
     (10, 46, 2), (5, None, None)],
)
def test_season_phase(game, season_games, phase):
    assert season_phase(game, season_games) == phase


@pytest.mark.parametrize(
    "season, status",
    [
        (SeasonSpan.starting(2024), "scheduled"),
        (SeasonSpan.starting(2023), "void"),
        (SeasonSpan("2026", 2026, 2026), "scheduled"),
        (SeasonSpan("2025", 2025, 2025), "void"),
    ],
)
def test_unplayed_status_by_season(db, season, status):
    loader = CsvLoader(db, current_season=2024, current_year=2026)
    assert loader._unplayed_status(season) == status
