"""Decision: pyramid Elo, design B (convert on move).

Decided in chunks 05a and 09 (2026-11-04). Each division keeps its own
1500-centred scale. A team moving within its country brings its last
rating minus an adjustment learned from earlier movers on that boundary:
seasons before the current one only, at least 5 samples, each measured
after 10 games. Otherwise a fallback seed: the mean of the N lowest
(promoted) or highest (relegated) returning ratings.
"""
import pytest

from scorecaster.config import FeatureConfig
from scorecaster.features.pyramid import (
    Boundary,
    MoveAdjustments,
    PyramidElo,
    _fallback,
)
from scorecaster.features.source import SeasonInfo

UP_INTO_E0 = Boundary("E0", "E1", promoted=True)


def season(id, code, tier, start, teams, competition_id=None):
    """Return an English SeasonInfo for the tests."""
    return SeasonInfo(
        id=id,
        competition_id=competition_id or tier,
        code=code,
        country="England",
        tier=tier,
        start_year=start,
        team_ids=frozenset(teams),
        previous_id=None,
        season_games=38,
    )


def test_adjustment_uses_only_earlier_seasons_and_needs_5_samples():
    adjustments = MoveAdjustments(min_samples=5)
    for year, shift in zip(range(2015, 2020), (100, 200, 300, 400, 500)):
        adjustments.add(UP_INTO_E0, year, shift)
    assert adjustments.adjustment(UP_INTO_E0, 2020) == 300
    assert adjustments.adjustment(UP_INTO_E0, 2019) is None


def test_fallback_seeds_from_the_lowest_or_highest_returning_teams():
    ratings = [1400.0, 1450.0, 1500.0, 1550.0, 1600.0]
    assert _fallback(ratings, 2, promoted=True, initial=1500) == 1425
    assert _fallback(ratings, 2, promoted=False, initial=1500) == 1575
    assert _fallback([], 3, promoted=True, initial=1500) == 1500


def promoted_team_rating(samples: int) -> float:
    """Promote team 1 (rated 1650 in E1) with `samples` earlier movers."""
    elo = PyramidElo(FeatureConfig())
    elo.open_season(season(1, "E1", 2, 2023, {1, 2}), None)
    elo.divisions[2].set(1, 1650.0)
    for year in range(2018, 2018 + samples):
        elo.adjustments.add(UP_INTO_E0, year, 200.0)
    e0_before = season(3, "E0", 1, 2023, {3, 4, 5})
    elo.open_season(e0_before, None)
    elo.divisions[1].set(3, 1450.0)
    elo.divisions[1].set(4, 1550.0)
    elo.open_season(season(4, "E0", 1, 2024, {1, 3, 4}), e0_before)
    return elo.rating(1, 1)


def test_mover_keeps_its_rating_minus_the_learned_adjustment():
    assert promoted_team_rating(samples=5) == 1450.0


def test_mover_gets_the_fallback_seed_until_enough_samples():
    # returning E0 teams after regression: 1460 and 1540; one newcomer
    assert promoted_team_rating(samples=4) == pytest.approx(1460.0)


def test_shift_is_measured_after_10_games_in_the_new_division():
    elo = PyramidElo(FeatureConfig())
    elo.open_season(season(1, "E1", 2, 2023, {1, 2}), None)
    elo.divisions[2].set(1, 1650.0)
    elo.open_season(season(2, "E0", 1, 2024, {1, 3}), None)
    for _ in range(9):
        elo.update(1, 1, 3, 0, 0)
    assert elo.adjustments.samples[UP_INTO_E0] == []
    elo.update(1, 1, 3, 0, 0)
    [(year, shift)] = elo.adjustments.samples[UP_INTO_E0]
    assert year == 2024
    assert shift == pytest.approx(1650.0 - elo.rating(1, 1))
