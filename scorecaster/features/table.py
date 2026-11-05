"""Rebuild league tables from results, and group positions into bands."""
from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Iterable


@dataclass
class TableRow:
    """One team's running line in a league table."""

    team_id: int
    played: int = 0
    won: int = 0
    drawn: int = 0
    lost: int = 0
    gf: int = 0
    ga: int = 0

    @property
    def points(self) -> int:
        """Return points: 3 per win, 1 per draw."""
        return self.won * 3 + self.drawn

    @property
    def gd(self) -> int:
        """Return goal difference."""
        return self.gf - self.ga

    def add(self, gf: int, ga: int) -> None:
        """Add one result, given goals for and against."""
        self.played += 1
        self.gf += gf
        self.ga += ga
        if gf > ga:
            self.won += 1
        elif gf == ga:
            self.drawn += 1
        else:
            self.lost += 1


class LeagueTable:
    """A league table ordered by points, goal difference, then goals."""

    def __init__(self, team_ids: Iterable[int] = ()) -> None:
        self.rows = {team_id: TableRow(team_id) for team_id in team_ids}

    def row(self, team_id: int) -> TableRow:
        """Return a team's row, adding an empty one if it isn't listed."""
        return self.rows.setdefault(team_id, TableRow(team_id))

    def apply(
        self, home_id: int, away_id: int, home_goals: int, away_goals: int
    ) -> None:
        """Add a finished match to both teams' rows."""
        self.row(home_id).add(home_goals, away_goals)
        self.row(away_id).add(away_goals, home_goals)

    def standings(self) -> list[TableRow]:
        """Return the rows in table order."""
        return sorted(self.rows.values(), key=_table_order)

    def position(self, team_id: int) -> int | None:
        """Return a team's 1-based position, or None before its first game."""
        if self.row(team_id).played == 0:
            return None
        for position, row in enumerate(self.standings(), start=1):
            if row.team_id == team_id:
                return position
        return None

    def final_position(self, team_id: int) -> int | None:
        """Return a team's position, or None if it isn't in this table."""
        if team_id not in self.rows:
            return None
        return self.position(team_id)

    def points_at(self, position: int) -> int | None:
        """Return the points of the team in a position, if it exists."""
        standings = self.standings()
        if 0 < position <= len(standings):
            return standings[position - 1].points
        return None

    def goals_per_team_game(self) -> float | None:
        """Return average goals scored per team per game so far."""
        played = sum(row.played for row in self.rows.values())
        if not played:
            return None
        return sum(row.gf for row in self.rows.values()) / played


def band_of(
    position: int | None, league_size: int, band_count: int
) -> int | None:
    """Return which of `band_count` equal slices of the table a position is in.

    Band 1 is the top. 20 teams, 5 bands: 1–4 -> 1, 5–8 -> 2, 17–20 -> 5.
    24 teams, 5 bands: 1–4 -> 1, 5–9 -> 2, 20–24 -> 5.
    """
    if position is None or league_size == 0:
        return None
    return ceil(position * band_count / league_size)


def _table_order(row: TableRow) -> tuple[int, int, int, int]:
    """Sort key: most points, then goal difference, then goals scored."""
    return (-row.points, -row.gd, -row.gf, row.team_id)
