"""Rate the teams of one division with goal-difference-weighted Elo."""
from __future__ import annotations

from typing import Iterable

from scorecaster.config import FeatureConfig


class EloRatings:
    """Elo ratings for the teams of one division, on a 1500-centred scale.

    Each result moves both teams by K × goal-difference multiplier ×
    (actual − expected score), with a fixed home advantage in the
    expectation. Each summer, returning teams are pulled part of the way
    back to 1500.
    """

    def __init__(self, cfg: FeatureConfig) -> None:
        self.cfg = cfg
        self.ratings: dict[int, float] = {}

    def __contains__(self, team_id: int) -> bool:
        return team_id in self.ratings

    def rating(self, team_id: int) -> float:
        """Return a team's rating, or the starting rating if it has none."""
        return self.ratings.get(team_id, self.cfg.elo_initial)

    def set(self, team_id: int, rating: float) -> None:
        """Give a team a rating, e.g. on joining the division."""
        self.ratings[team_id] = rating

    def remove(self, team_id: int) -> float:
        """Take a team out of the division and return its last rating."""
        return self.ratings.pop(team_id)

    def discard(self, team_id: int) -> None:
        """Take a team out of the division if it is there."""
        self.ratings.pop(team_id, None)

    def expected(self, team_id: int, opponent_id: int, is_home: bool) -> float:
        """Return the team's expected score (0–1) against the opponent."""
        advantage = self.cfg.elo_home_advantage
        if not is_home:
            advantage = -advantage
        difference = (
            self.rating(team_id) + advantage - self.rating(opponent_id)
        )
        return 1.0 / (1.0 + 10 ** (-difference / 400.0))

    def update(
        self, home_id: int, away_id: int, home_goals: int, away_goals: int
    ) -> None:
        """Move both ratings after a result."""
        expected = self.expected(home_id, away_id, is_home=True)
        delta = (
            self.cfg.elo_k
            * _margin_multiplier(abs(home_goals - away_goals))
            * (_actual_score(home_goals, away_goals) - expected)
        )
        self.ratings[home_id] = self.rating(home_id) + delta
        self.ratings[away_id] = self.rating(away_id) - delta

    def regress(self, team_ids: Iterable[int]) -> None:
        """Pull the given teams part of the way back to the starting rating."""
        weight = self.cfg.elo_season_regression
        for team_id in team_ids:
            rating = self.rating(team_id)
            self.ratings[team_id] = (
                rating + weight * (self.cfg.elo_initial - rating)
            )


def _actual_score(home_goals: int, away_goals: int) -> float:
    """Return the home side's score: 1 for a win, 0.5 a draw, 0 a loss."""
    if home_goals > away_goals:
        return 1.0
    return 0.5 if home_goals == away_goals else 0.0


def _margin_multiplier(margin: int) -> float:
    """Scale a rating change by the winning margin: 1, 1.5, then (11+m)/8."""
    if margin <= 1:
        return 1.0
    if margin == 2:
        return 1.5
    return (11 + margin) / 8
