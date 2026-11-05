"""Decision: the Elo formula.

Goal-difference-weighted Elo, carried over from the first build: K 20,
home advantage 60, margin multiplier 1 / 1.5 / (11 + m) / 8, and a 20%
pull back to 1500 each summer (toward 1500 rather than the pool mean
since chunk 09). Change these deliberately and update this file with it.
"""
import pytest

from scorecaster.config import FeatureConfig
from scorecaster.features.elo import EloRatings, _margin_multiplier


def test_equal_teams_home_side_expects_about_59_percent():
    elo = EloRatings(FeatureConfig())
    assert elo.expected(1, 2, is_home=True) == pytest.approx(0.58548, 1e-4)
    assert elo.expected(1, 2, is_home=False) == pytest.approx(
        1 - 0.58548, 1e-4
    )


def test_one_goal_home_win_between_equals_moves_about_8_points():
    elo = EloRatings(FeatureConfig())
    elo.set(1, 1500.0)
    elo.set(2, 1500.0)
    elo.update(1, 2, home_goals=1, away_goals=0)
    assert elo.rating(1) == pytest.approx(1508.29, abs=0.01)
    assert elo.rating(1) + elo.rating(2) == pytest.approx(3000.0)


@pytest.mark.parametrize(
    "margin, multiplier", [(0, 1.0), (1, 1.0), (2, 1.5), (3, 1.75)]
)
def test_margin_multiplier(margin, multiplier):
    assert _margin_multiplier(margin) == multiplier


def test_summer_regression_pulls_20_percent_back_to_1500():
    elo = EloRatings(FeatureConfig())
    elo.set(1, 1600.0)
    elo.set(2, 1400.0)
    elo.regress([1, 2])
    assert (elo.rating(1), elo.rating(2)) == (1580.0, 1420.0)
