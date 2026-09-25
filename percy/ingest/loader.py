"""Orchestrates pulling seasons from a provider into the local database."""
from __future__ import annotations

import logging
from datetime import date

from percy.api.base import FootballDataProvider
from percy.db import Database, Team
from percy.ingest.records import CompetitionRecord, SeasonBundle, TeamRecord
from percy.ingest.repository import RawDataRepository, SaveStats

log = logging.getLogger(__name__)


class HistoricalLoader:
    """Loads a competition and a set of seasons; safe to re-run."""

    def __init__(self, provider: FootballDataProvider, db: Database, today: date | None = None) -> None:
        self.provider = provider
        self.db = db
        self.today = today or date.today()

    def load(self, competition_code: str, start_years: list[int], refresh_current: bool = False) -> SaveStats:
        """Fetch and store each season; only unfinished seasons are re-requested when `refresh_current`."""
        total = SaveStats()
        competition = self.provider.competition(competition_code)
        with self.db.session() as s:
            RawDataRepository(s).save_competition(competition)
        for year in start_years:
            refresh = refresh_current and not self._season_complete(competition, year)
            bundle = self.provider.season(competition, year, refresh=refresh)
            stats = self._store(competition, bundle)
            log.info("season %s: %s", year, stats)
            total.inserted += stats.inserted
            total.updated += stats.updated
            total.skipped += stats.skipped
        return total

    def _season_complete(self, competition: CompetitionRecord, year: int) -> bool:
        season = next((s for s in competition.seasons if s.start_year == year), None)
        return bool(season and season.end_date and season.end_date < self.today)

    def _store(self, competition: CompetitionRecord, bundle: SeasonBundle) -> SaveStats:
        with self.db.session() as s:
            repo = RawDataRepository(s)
            repo.save_season(bundle.season)
            for team in bundle.teams:
                repo.save_team(team, bundle.season.id)
            for match in bundle.matches:
                for team_id in (match.home_team_id, match.away_team_id):
                    if s.get(Team, team_id) is None:
                        repo.save_team(TeamRecord(id=team_id, name=f"Team {team_id}"), bundle.season.id)
                repo.save_match(match)
            return repo.stats
