"""Shared fixtures: in-memory database, fake API client and synthetic match helpers."""
import json
from datetime import datetime
from pathlib import Path

import pytest

from percy.api.base import JsonClient
from percy.db import Competition, Database, Match, Season, SeasonTeam, Team

FIXTURES = Path(__file__).parent / "fixtures"


class FakeJsonClient(JsonClient):
    """Serves fixture files keyed by path and season; records calls."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, dict | None, bool]] = []

    def get(self, path, params=None, refresh=False):
        self.calls.append((path, params, refresh))
        name = path.replace("competitions/", "").split("/")
        stem = f"{name[1]}_{name[0]}_{params['season']}" if len(name) > 1 else f"competition_{name[0]}"
        return json.loads((FIXTURES / f"{stem}.json").read_text())


@pytest.fixture
def db(tmp_path):
    database = Database.for_path(tmp_path / "test.db")
    database.create_schema()
    return database


@pytest.fixture
def fake_client():
    return FakeJsonClient()


class LeagueFactory:
    """Creates a competition, seasons, teams and matches directly in the database."""

    def __init__(self, db: Database) -> None:
        self.db = db
        self._next_id = 1
        with db.session() as s:
            s.add(Competition(id=1, name="Test League", code="TL"))

    def season(self, season_id: int, year: int, team_ids: list[int]) -> None:
        with self.db.session() as s:
            s.add(Season(id=season_id, competition_id=1, start_year=year))
            for t in team_ids:
                if s.get(Team, t) is None:
                    s.add(Team(id=t, name=f"T{t}"))
            s.flush()
            s.add_all(SeasonTeam(season_id=season_id, team_id=t) for t in team_ids)

    def match(self, season_id: int, when: str, home: int, away: int, score: tuple[int, int] | None) -> int:
        mid = self._next_id
        self._next_id += 1
        with self.db.session() as s:
            s.add(Match(id=mid, competition_id=1, season_id=season_id, utc_date=datetime.fromisoformat(when),
                        status="FINISHED" if score else "SCHEDULED", home_team_id=home, away_team_id=away,
                        ft_home=score[0] if score else None, ft_away=score[1] if score else None))
        return mid

    def finish(self, match_id: int, score: tuple[int, int]) -> None:
        with self.db.session() as s:
            m = s.get(Match, match_id)
            m.status, m.ft_home, m.ft_away = "FINISHED", *score


@pytest.fixture
def league(db):
    return LeagueFactory(db)
