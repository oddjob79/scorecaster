"""Replay matches in date order, keeping everything known before each day.

Features for a day's matches are read before that day's results are
applied, so no feature ever sees its own match's result.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date

from scorecaster.config import FeatureConfig
from scorecaster.db import Match
from scorecaster.features.history import (
    MatchStats,
    TeamHistory,
    TeamMatchRecord,
)
from scorecaster.features.market import MarketProbabilities
from scorecaster.features.pyramid import PyramidElo
from scorecaster.features.source import SeasonInfo
from scorecaster.features.table import LeagueTable, band_of


class LeagueState:
    """Histories, league tables and Elo, as of the start of a day.

    `market` holds each match's pre-match market probabilities, which are
    known before kick-off and so safe to read for that match.
    """

    def __init__(
        self,
        cfg: FeatureConfig,
        seasons: dict[int, SeasonInfo],
        market: dict[int, MarketProbabilities] | None = None,
    ) -> None:
        self.cfg = cfg
        self.seasons = seasons
        self.market = market or {}
        self.histories: dict[int, TeamHistory] = defaultdict(TeamHistory)
        self.tables: dict[int, LeagueTable] = {}
        self.elo = PyramidElo(cfg)

    def table(self, season_id: int) -> LeagueTable:
        """Return a season's table, opening the season on first use."""
        if season_id not in self.tables:
            self._open_season(self.seasons[season_id])
        return self.tables[season_id]

    def previous_table(self, season_id: int) -> LeagueTable | None:
        """Return the table of the competition's previous season, if seen."""
        previous_id = self.seasons[season_id].previous_id
        return self.tables.get(previous_id)

    def previous_position(
        self, team_id: int, season_id: int
    ) -> int | None:
        """Return the team's final position in the previous season."""
        previous = self.previous_table(season_id)
        return previous.final_position(team_id) if previous else None

    def season_games(self, season_id: int) -> int | None:
        """Return how many games each team plays in the season."""
        return self.seasons[season_id].season_games

    def band(self, team_id: int, season_id: int) -> int | None:
        """Return the team's position band (1 = top fifth).

        Before its first game, last season's final band in this league is
        used; a team new to the league starts in the bottom band.
        """
        band_count = self.cfg.position_band_count
        table = self.table(season_id)
        position = table.position(team_id)
        if position is not None:
            return band_of(position, len(table.rows), band_count)
        previous = self.previous_table(season_id)
        if previous is None:
            return None
        final = previous.final_position(team_id)
        if final is None:
            return band_count
        return band_of(final, len(previous.rows), band_count)

    def start_day(self, matches: list[Match]) -> None:
        """Open any season first seen today, before features are read."""
        for season_id in dict.fromkeys(m.season_id for m in matches):
            self.table(season_id)

    def apply_day(self, matches: list[Match]) -> None:
        """Apply the day's results, after features have been read."""
        finished = [m for m in matches if m.is_finished]
        bands_before = {
            (match.id, team_id): self.band(team_id, match.season_id)
            for match in finished
            for team_id in (match.home_team_id, match.away_team_id)
        }
        for match in finished:
            self._add_records(match, bands_before)
            self.tables[match.season_id].apply(
                match.home_team_id,
                match.away_team_id,
                match.ft_home,
                match.ft_away,
            )
            self.elo.update(
                match.competition_id,
                match.home_team_id,
                match.away_team_id,
                match.ft_home,
                match.ft_away,
            )

    def _open_season(self, season: SeasonInfo) -> None:
        """Create the season's table and start its Elo season."""
        previous = self.seasons.get(season.previous_id)
        self.elo.open_season(season, previous)
        self.tables[season.id] = LeagueTable(season.team_ids)

    def _add_records(
        self, match: Match, bands_before: dict[tuple[int, int], int | None]
    ) -> None:
        """Add the match to both teams' histories."""
        sides = (
            (match.home_team_id, match.away_team_id, match.ft_home,
             match.ft_away, True),
            (match.away_team_id, match.home_team_id, match.ft_away,
             match.ft_home, False),
        )
        home_stats, away_stats = _match_stats(match)
        stats = {
            match.home_team_id: (home_stats, away_stats),
            match.away_team_id: (away_stats, home_stats),
        }
        for team_id, opponent_id, gf, ga, is_home in sides:
            stats_for, stats_against = stats[team_id]
            self.histories[team_id].add(
                TeamMatchRecord(
                    match_id=match.id,
                    day=match.match_date,
                    season_id=match.season_id,
                    is_home=is_home,
                    opponent_id=opponent_id,
                    gf=gf,
                    ga=ga,
                    opponent_band=bands_before[(match.id, opponent_id)],
                    stats_for=stats_for,
                    stats_against=stats_against,
                )
            )


@dataclass(frozen=True)
class MatchContext:
    """A match seen from one team's side, with the state before kick-off."""

    match: Match
    team_id: int
    opponent_id: int
    is_home: bool
    state: LeagueState

    @classmethod
    def for_side(
        cls, match: Match, is_home: bool, state: LeagueState
    ) -> MatchContext:
        """Return the context for the home (True) or away (False) team."""
        if is_home:
            team_id, opponent_id = match.home_team_id, match.away_team_id
        else:
            team_id, opponent_id = match.away_team_id, match.home_team_id
        return cls(match, team_id, opponent_id, is_home, state)

    @property
    def day(self) -> date:
        """Return the match date."""
        return self.match.match_date

    @property
    def season_id(self) -> int:
        """Return the match's season id."""
        return self.match.season_id

    @property
    def competition_id(self) -> int:
        """Return the match's competition id."""
        return self.match.competition_id

    @property
    def history(self) -> TeamHistory:
        """Return this team's history so far."""
        return self.state.histories[self.team_id]

    @property
    def table(self) -> LeagueTable:
        """Return the season's table so far."""
        return self.state.table(self.season_id)


def _match_stats(match: Match) -> tuple[MatchStats, MatchStats]:
    """Return the (home, away) match stats from a stored match."""
    home = MatchStats(
        shots=match.home_shots,
        shots_on_target=match.home_shots_on_target,
        corners=match.home_corners,
        fouls=match.home_fouls,
        yellows=match.home_yellows,
        reds=match.home_reds,
    )
    away = MatchStats(
        shots=match.away_shots,
        shots_on_target=match.away_shots_on_target,
        corners=match.away_corners,
        fouls=match.away_fouls,
        yellows=match.away_yellows,
        reds=match.away_reds,
    )
    return home, away


def safe_div(numerator: float, denominator: float) -> float | None:
    """Divide, returning None when the denominator is zero."""
    return numerator / denominator if denominator else None
