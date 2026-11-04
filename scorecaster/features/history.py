"""Keep each team's finished matches in date order."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Callable


@dataclass(frozen=True)
class TeamMatchRecord:
    """One finished match from one team's side.

    `opponent_band` is the opponent's position band just before the match,
    used for the record against similar opponents.
    """

    match_id: int
    day: date
    season_id: int
    is_home: bool
    opponent_id: int
    gf: int
    ga: int
    opponent_band: int | None

    @property
    def points(self) -> int:
        """Return league points: 3 for a win, 1 for a draw, 0 for a loss."""
        if self.won:
            return 3
        return 1 if self.drawn else 0

    @property
    def won(self) -> bool:
        """Return True for a win."""
        return self.gf > self.ga

    @property
    def drawn(self) -> bool:
        """Return True for a draw."""
        return self.gf == self.ga

    @property
    def lost(self) -> bool:
        """Return True for a loss."""
        return self.gf < self.ga


class TeamHistory:
    """A team's finished matches, oldest first."""

    def __init__(self) -> None:
        self.records: list[TeamMatchRecord] = []

    def __len__(self) -> int:
        return len(self.records)

    def add(self, record: TeamMatchRecord) -> None:
        """Append a match that has just finished."""
        self.records.append(record)

    def last(
        self,
        count: int | None = None,
        venue: bool | None = None,
        where: Callable[[TeamMatchRecord], bool] | None = None,
    ) -> list[TeamMatchRecord]:
        """Return the most recent matching records, oldest first.

        `venue` True keeps home matches and False away matches. `where`
        filters further, e.g. matches against one opponent. Without
        `count`, every matching record is returned.
        """
        found: list[TeamMatchRecord] = []
        for record in reversed(self.records):
            if venue is not None and record.is_home != venue:
                continue
            if where is not None and not where(record):
                continue
            found.append(record)
            if count is not None and len(found) == count:
                break
        found.reverse()
        return found

    def season(self, season_id: int) -> list[TeamMatchRecord]:
        """Return the team's records in one season."""
        return [r for r in self.records if r.season_id == season_id]
