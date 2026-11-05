"""Run Elo across a country's divisions, carrying ratings between them.

Each division keeps its own 1500-centred scale (`EloRatings`). A team that
changes division within its country brings its last rating, minus an
adjustment learned from earlier teams that made the same move. A team
with nothing to bring (new to the data, or from a league not loaded)
gets a fallback seed from its new division's ratings.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from statistics import mean

from scorecaster.config import FeatureConfig
from scorecaster.features.elo import EloRatings
from scorecaster.features.source import SeasonInfo


@dataclass(frozen=True)
class Boundary:
    """A move between two divisions: into `to_code` from `from_code`."""

    to_code: str
    from_code: str
    promoted: bool


@dataclass
class PendingMove:
    """A move whose size is measured once the team has played enough."""

    boundary: Boundary
    season_start: int
    rating_before: float
    games: int = 0


class MoveAdjustments:
    """Learn how much a rating shifts when a team crosses each boundary.

    A sample is (rating at the end of the old season) − (rating after the
    first N games in the new division). The adjustment for a season is
    the mean of samples from earlier seasons only, so nothing later
    leaks into it. Too few samples means no adjustment yet.
    """

    def __init__(self, min_samples: int) -> None:
        self.min_samples = min_samples
        self.samples: dict[Boundary, list[tuple[int, float]]] = (
            defaultdict(list)
        )

    def add(self, boundary: Boundary, season_start: int, shift: float) -> None:
        """Record one mover's measured shift."""
        self.samples[boundary].append((season_start, shift))

    def adjustment(
        self, boundary: Boundary, season_start: int
    ) -> float | None:
        """Return the mean shift from seasons before `season_start`."""
        earlier = [
            shift
            for start, shift in self.samples[boundary]
            if start < season_start
        ]
        if len(earlier) < self.min_samples:
            return None
        return mean(earlier)


class PyramidElo:
    """Elo for every division, with ratings carried when teams move."""

    def __init__(self, cfg: FeatureConfig) -> None:
        self.cfg = cfg
        self.divisions: dict[int, EloRatings] = {}
        self.current_division: dict[int, SeasonInfo] = {}
        self.adjustments = MoveAdjustments(cfg.elo_min_movers)
        self.pending: dict[int, PendingMove] = {}

    def rating(self, team_id: int, competition_id: int) -> float:
        """Return a team's rating in a division."""
        return self._division(competition_id).rating(team_id)

    def expected(
        self,
        team_id: int,
        opponent_id: int,
        is_home: bool,
        competition_id: int,
    ) -> float:
        """Return the team's expected score (0–1) in a division match."""
        division = self._division(competition_id)
        return division.expected(team_id, opponent_id, is_home)

    def open_season(
        self, season: SeasonInfo, previous: SeasonInfo | None
    ) -> None:
        """Start a season: regress returning teams, then place newcomers.

        Returning teams are those in the division's previous season. Every
        other team in the season is a newcomer.
        """
        division = self._division(season.competition_id)
        returning = previous.team_ids if previous else frozenset()
        stayers = [t for t in season.team_ids if t in returning]
        newcomers = [t for t in season.team_ids if t not in returning]
        division.regress(stayers)
        stayer_ratings = sorted(division.rating(t) for t in stayers)
        for team_id in newcomers:
            rating = self._arrival_rating(
                team_id, season, stayer_ratings, len(newcomers)
            )
            division.set(team_id, rating)
            self.current_division[team_id] = season
        for team_id in stayers:
            self.current_division[team_id] = season

    def update(
        self,
        competition_id: int,
        home_id: int,
        away_id: int,
        home_goals: int,
        away_goals: int,
    ) -> None:
        """Apply a result, and measure any mover that has played enough.

        Both teams must belong to the division. A match between divisions,
        such as a cup tie, would otherwise move one team on the wrong
        scale, so it raises instead.
        """
        division = self._division(competition_id)
        for team_id in (home_id, away_id):
            if team_id not in division:
                raise ValueError(
                    f"team {team_id} isn't in division {competition_id}; "
                    "cross-division matches aren't supported by pyramid Elo"
                )
        division.update(home_id, away_id, home_goals, away_goals)
        for team_id in (home_id, away_id):
            self._count_mover_game(team_id, division)

    def _arrival_rating(
        self,
        team_id: int,
        season: SeasonInfo,
        stayer_ratings: list[float],
        newcomer_count: int,
    ) -> float:
        """Return a newcomer's first rating in its new division."""
        old = self.current_division.get(team_id)
        if not _moved_within_country(old, season):
            if old is not None:
                self._division(old.competition_id).discard(team_id)
            return _fallback(
                stayer_ratings,
                newcomer_count,
                promoted=True,
                initial=self.cfg.elo_initial,
            )

        boundary = Boundary(season.code, old.code, old.tier > season.tier)
        rating_before = self._division(old.competition_id).remove(team_id)
        self.pending[team_id] = PendingMove(
            boundary, season.start_year, rating_before
        )
        shift = self.adjustments.adjustment(boundary, season.start_year)
        if shift is None:
            return _fallback(
                stayer_ratings,
                newcomer_count,
                promoted=boundary.promoted,
                initial=self.cfg.elo_initial,
            )
        return rating_before - shift

    def _count_mover_game(self, team_id: int, division: EloRatings) -> None:
        """Count a mover's game; after N games, record its rating shift."""
        move = self.pending.get(team_id)
        if move is None:
            return
        move.games += 1
        if move.games == self.cfg.elo_mover_games:
            shift = move.rating_before - division.rating(team_id)
            self.adjustments.add(move.boundary, move.season_start, shift)
            del self.pending[team_id]

    def _division(self, competition_id: int) -> EloRatings:
        """Return a division's ratings, creating them on first use."""
        if competition_id not in self.divisions:
            self.divisions[competition_id] = EloRatings(self.cfg)
        return self.divisions[competition_id]


def _moved_within_country(
    old: SeasonInfo | None, season: SeasonInfo
) -> bool:
    """Return True when a team comes from another tier of the same country."""
    return (
        old is not None
        and old.country == season.country
        and old.tier != season.tier
    )


def _fallback(
    stayer_ratings: list[float],
    newcomer_count: int,
    promoted: bool,
    initial: float,
) -> float:
    """Return a seed from the division's own ratings.

    Promoted (or unknown) teams get the mean of the N lowest-rated
    returning teams, relegated teams the mean of the N highest, where N is
    the number of newcomers. An empty division starts everyone at
    `initial`.
    """
    if not stayer_ratings:
        return initial
    count = min(newcomer_count, len(stayer_ratings))
    if promoted:
        return mean(stayer_ratings[:count])
    return mean(stayer_ratings[-count:])
