"""Replays stored matches in date order and writes pre-match features for each team."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from itertools import groupby

from sqlalchemy import delete, select

from percy.config import FeatureConfig
from percy.db import Database, Match, Season, SeasonTeam
from percy.features.calculators import FeatureCalculator, default_calculators
from percy.features.schema import FeatureTableSchema
from percy.features.state import LeagueState, MatchContext

log = logging.getLogger(__name__)

FEATURE_STATUSES = ("FINISHED", "SCHEDULED", "TIMED")


@dataclass
class BuildStats:
    inserted: int = 0
    replaced: int = 0
    unchanged: int = 0


class MatchSource:
    """Reads matches, seasons and season membership needed for a build."""

    def __init__(self, db: Database, competition_id: int | None = None) -> None:
        self.db = db
        self.competition_id = competition_id

    def matches(self) -> list[Match]:
        with self.db.session() as s:
            q = select(Match).where(Match.status.in_(FEATURE_STATUSES)).order_by(Match.utc_date, Match.id)
            if self.competition_id is not None:
                q = q.where(Match.competition_id == self.competition_id)
            return list(s.scalars(q))

    def season_teams(self) -> dict[int, set[int]]:
        out: dict[int, set[int]] = {}
        with self.db.session() as s:
            for row in s.scalars(select(SeasonTeam)):
                out.setdefault(row.season_id, set()).add(row.team_id)
        return out

    def previous_seasons(self) -> dict[int, int | None]:
        """Map each season id to the preceding season of the same competition."""
        out: dict[int, int | None] = {}
        with self.db.session() as s:
            seasons = s.scalars(select(Season).order_by(Season.competition_id, Season.start_year)).all()
        for _, group in groupby(seasons, key=lambda x: x.competition_id):
            prev = None
            for season in group:
                out[season.id] = prev
                prev = season.id
        return out


class FeatureBuilder:
    """Builds `team_match_features` incrementally: new matches are inserted, pre-result rows refreshed."""

    def __init__(self, db: Database, cfg: FeatureConfig | None = None,
                 calculators: list[FeatureCalculator] | None = None, source: MatchSource | None = None) -> None:
        self.db = db
        self.cfg = cfg or FeatureConfig()
        self.calculators = calculators or default_calculators(self.cfg)
        self.schema = FeatureTableSchema([c for calc in self.calculators for c in calc.columns()])
        self.source = source or MatchSource(db)

    def build(self, rebuild: bool = False) -> BuildStats:
        """Compute features for all eligible matches; `rebuild` drops and recreates the derived table."""
        self._prepare_table(rebuild)
        final = self._final_match_ids()
        state = LeagueState(self.cfg, self.source.season_teams(), self.source.previous_seasons())
        rows: list[dict] = []
        stats = BuildStats()
        matches = self.source.matches()
        self._purge_stale({m.id for m in matches})
        for _, day_matches in groupby(matches, key=lambda m: m.utc_date.date()):
            day_matches = list(day_matches)
            state.start_day(day_matches)
            for match in day_matches:
                if match.id in final:
                    stats.unchanged += 1
                    continue
                rows.extend(self._rows_for(match, state))
            state.apply_day(day_matches)
        self._write(rows, stats)
        return stats

    def _prepare_table(self, rebuild: bool) -> None:
        if rebuild:
            self.schema.drop(self.db.engine)
        elif not self.schema.matches_database(self.db.engine) and self._table_exists():
            raise RuntimeError("feature columns changed; run with --rebuild to recreate the derived table")
        self.schema.create(self.db.engine)

    def _table_exists(self) -> bool:
        return self.schema.table.name in self.db.existing_tables()

    def _final_match_ids(self) -> set[int]:
        """Matches whose stored rows were computed after the result was known."""
        t = self.schema.table
        with self.db.engine.connect() as conn:
            return {r.match_id for r in conn.execute(select(t.c.match_id).where(t.c.is_finished).distinct())}

    def _purge_stale(self, eligible_ids: set[int]) -> None:
        """Remove pre-result rows for fixtures no longer eligible (e.g. postponed)."""
        t = self.schema.table
        with self.db.engine.begin() as conn:
            stale = [r.match_id for r in conn.execute(select(t.c.match_id).where(~t.c.is_finished))
                     if r.match_id not in eligible_ids]
            if stale:
                conn.execute(delete(t).where(t.c.match_id.in_(stale)))

    def _rows_for(self, match: Match, state: LeagueState) -> list[dict]:
        rows = []
        for is_home in (True, False):
            ctx = MatchContext.for_side(match, is_home, state)
            gf, ga = (match.ft_home, match.ft_away) if is_home else (match.ft_away, match.ft_home)
            finished = match.is_finished
            row = {
                "match_id": match.id, "team_id": ctx.team_id, "opponent_id": ctx.opponent_id,
                "competition_id": match.competition_id, "season_id": match.season_id,
                "match_date": ctx.day, "matchday": match.matchday, "is_home": is_home, "is_finished": finished,
                "goals_for": gf if finished else None, "goals_against": ga if finished else None,
                "result_pts": (3 if gf > ga else 1 if gf == ga else 0) if finished else None,
            }
            for calc in self.calculators:
                row.update(calc.compute(ctx))
            rows.append(row)
        return rows

    def _write(self, rows: list[dict], stats: BuildStats) -> None:
        if not rows:
            return
        t = self.schema.table
        ids = sorted({r["match_id"] for r in rows})
        with self.db.engine.begin() as conn:
            existing = set()
            for i in range(0, len(ids), 500):
                chunk = ids[i:i + 500]
                existing |= {r.match_id for r in conn.execute(select(t.c.match_id).where(t.c.match_id.in_(chunk)))}
                conn.execute(delete(t).where(t.c.match_id.in_(chunk)))
            conn.execute(t.insert(), rows)
        stats.replaced = len(existing)
        stats.inserted = len(ids) - len(existing)
        log.info("features: %s", stats)
