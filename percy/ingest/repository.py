"""Persistence of provider records into the raw tables."""
from __future__ import annotations

from dataclasses import asdict, dataclass

from sqlalchemy.orm import Session

from percy.db import Area, Competition, Match, Season, SeasonTeam, Team
from percy.ingest.records import AreaRecord, CompetitionRecord, MatchRecord, SeasonRecord, TeamRecord


@dataclass
class SaveStats:
    """Counts of rows written during a load."""

    inserted: int = 0
    updated: int = 0
    skipped: int = 0


class RawDataRepository:
    """Insert-only writes for reference data; matches update only until they are finished."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.stats = SaveStats()

    def _insert_if_missing(self, model, **values) -> None:
        if self.session.get(model, values["id"]) is None:
            self.session.add(model(**values))
            self.stats.inserted += 1
        else:
            self.stats.skipped += 1

    def save_area(self, area: AreaRecord | None) -> None:
        if area is not None:
            self._insert_if_missing(Area, **asdict(area))
            self.session.flush()

    def save_competition(self, comp: CompetitionRecord) -> None:
        self.save_area(comp.area)
        self._insert_if_missing(Competition, id=comp.id, area_id=comp.area.id if comp.area else None,
                                name=comp.name, code=comp.code, type=comp.type, emblem=comp.emblem)
        self.session.flush()

    def save_season(self, season: SeasonRecord) -> None:
        existing = self.session.get(Season, season.id)
        if existing is None:
            self.session.add(Season(**asdict(season)))
            self.stats.inserted += 1
        elif existing.winner_team_id is None and season.winner_team_id is not None:
            existing.winner_team_id = season.winner_team_id
            self.stats.updated += 1
        self.session.flush()

    def save_team(self, team: TeamRecord, season_id: int | None = None) -> None:
        self.save_area(team.area)
        values = asdict(team)
        values.pop("area")
        self._insert_if_missing(Team, area_id=team.area.id if team.area else None, **values)
        self.session.flush()
        if season_id is not None and self.session.get(SeasonTeam, (season_id, team.id)) is None:
            self.session.add(SeasonTeam(season_id=season_id, team_id=team.id))

    def save_match(self, match: MatchRecord) -> None:
        existing = self.session.get(Match, match.id)
        if existing is None:
            self.session.add(Match(**asdict(match)))
            self.stats.inserted += 1
        elif existing.is_finished:
            self.stats.skipped += 1
        else:
            for key, value in asdict(match).items():
                setattr(existing, key, value)
            self.stats.updated += 1
