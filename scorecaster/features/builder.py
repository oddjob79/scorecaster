"""Replay stored matches in date order and write pre-match features.

Rows are kept up to date incrementally: a match whose features were
computed after its result is final and never recomputed; a scheduled
match's row is recomputed on every build, so it reflects the latest
results. The whole history is still replayed each time, because every
feature depends on what came before.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from itertools import groupby

from sqlalchemy import delete, select

from scorecaster.config import FeatureConfig
from scorecaster.db import Database, Match
from scorecaster.features.calculators import (
    FeatureCalculator,
    default_calculators,
)
from scorecaster.features.schema import FeatureTableSchema
from scorecaster.features.source import MatchSource
from scorecaster.features.state import LeagueState, MatchContext

log = logging.getLogger(__name__)

ROWS_PER_WRITE = 20_000
IDS_PER_DELETE = 500


@dataclass
class BuildStats:
    """Counts of matches inserted, replaced and left unchanged."""

    inserted: int = 0
    replaced: int = 0
    unchanged: int = 0


class FeatureBuilder:
    """Build the `team_match_features` table from the stored matches."""

    def __init__(
        self,
        db: Database,
        cfg: FeatureConfig | None = None,
        calculators: list[FeatureCalculator] | None = None,
        source: MatchSource | None = None,
    ) -> None:
        self.db = db
        self.cfg = cfg or FeatureConfig()
        self.calculators = calculators or default_calculators(self.cfg)
        self.schema = FeatureTableSchema(
            [name for calc in self.calculators for name in calc.columns()]
        )
        self.source = source or MatchSource(db)

    def build(self) -> BuildStats:
        """Add rows for new matches and refresh rows of scheduled ones.

        Raises an error if the calculators' columns differ from the stored
        table's; `rebuild` is needed then.
        """
        stored = self.schema.table.name in self.db.existing_tables()
        if stored and not self.schema.matches_database(self.db.engine):
            raise RuntimeError(
                "feature columns changed; run with --rebuild to recreate "
                "the derived table"
            )
        self.schema.create(self.db.engine)
        return self._replay()

    def rebuild(self) -> BuildStats:
        """Drop the feature table and build every row from scratch."""
        self.schema.drop(self.db.engine)
        self.schema.create(self.db.engine)
        return self._replay()

    def _replay(self) -> BuildStats:
        """Replay every match day, writing rows in batches."""
        final_ids = self._final_match_ids()
        state = LeagueState(
            self.cfg, self.source.seasons(), self.source.market()
        )
        matches = self.source.matches()
        self._purge_stale({match.id for match in matches})

        stats = BuildStats()
        rows: list[dict] = []
        for _, day in groupby(matches, key=_match_date):
            day_matches = list(day)
            state.start_day(day_matches)
            for match in day_matches:
                if match.id in final_ids:
                    stats.unchanged += 1
                else:
                    rows.extend(self._rows_for(match, state))
            state.apply_day(day_matches)
            if len(rows) >= ROWS_PER_WRITE:
                self._write(rows, stats)
                rows = []
        self._write(rows, stats)
        log.info("features: %s", stats)
        return stats

    def _final_match_ids(self) -> set[int]:
        """Return matches whose stored rows were computed after the result."""
        table = self.schema.table
        query = select(table.c.match_id).where(table.c.is_finished).distinct()
        with self.db.engine.connect() as connection:
            return {row.match_id for row in connection.execute(query)}

    def _purge_stale(self, eligible_ids: set[int]) -> None:
        """Delete pre-result rows for matches no longer scheduled.

        A fixture can drop out, e.g. when a match is voided.
        """
        table = self.schema.table
        with self.db.engine.begin() as connection:
            pending = connection.execute(
                select(table.c.match_id).where(~table.c.is_finished)
            )
            stale = [
                row.match_id
                for row in pending
                if row.match_id not in eligible_ids
            ]
            if stale:
                connection.execute(
                    delete(table).where(table.c.match_id.in_(stale))
                )

    def _rows_for(self, match: Match, state: LeagueState) -> list[dict]:
        """Return the two rows (home side, away side) for one match."""
        rows = []
        for is_home in (True, False):
            context = MatchContext.for_side(match, is_home, state)
            row = _context_columns(match, context)
            for calculator in self.calculators:
                row.update(calculator.compute(context))
            rows.append(row)
        return rows

    def _write(self, rows: list[dict], stats: BuildStats) -> None:
        """Replace any stored rows for these matches, then insert them."""
        if not rows:
            return
        table = self.schema.table
        match_ids = sorted({row["match_id"] for row in rows})
        existing: set[int] = set()
        with self.db.engine.begin() as connection:
            for start in range(0, len(match_ids), IDS_PER_DELETE):
                batch = match_ids[start:start + IDS_PER_DELETE]
                stored = connection.execute(
                    select(table.c.match_id).where(
                        table.c.match_id.in_(batch)
                    )
                )
                existing |= {row.match_id for row in stored}
                connection.execute(
                    delete(table).where(table.c.match_id.in_(batch))
                )
            connection.execute(table.insert(), rows)
        stats.replaced += len(existing)
        stats.inserted += len(match_ids) - len(existing)


def _context_columns(match: Match, context: MatchContext) -> dict:
    """Return the identifying and target columns for one side's row."""
    if context.is_home:
        goals_for, goals_against = match.ft_home, match.ft_away
    else:
        goals_for, goals_against = match.ft_away, match.ft_home
    finished = match.is_finished
    return {
        "match_id": match.id,
        "team_id": context.team_id,
        "opponent_id": context.opponent_id,
        "competition_id": match.competition_id,
        "season_id": match.season_id,
        "match_date": match.match_date,
        "is_home": context.is_home,
        "is_finished": finished,
        "goals_for": goals_for if finished else None,
        "goals_against": goals_against if finished else None,
        "result_pts": _points(goals_for, goals_against) if finished else None,
    }


def _points(goals_for: int, goals_against: int) -> int:
    """Return league points for a score: 3, 1 or 0."""
    if goals_for > goals_against:
        return 3
    return 1 if goals_for == goals_against else 0


def _match_date(match: Match):
    """Return a match's date, for grouping matches by day."""
    return match.match_date
