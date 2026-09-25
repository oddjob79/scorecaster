"""football-data.org v4 provider: endpoint calls and JSON-to-record parsing."""
from __future__ import annotations

from datetime import date, datetime

from percy.api.base import FootballDataProvider, JsonClient
from percy.api.http import HttpJsonClient, RateLimiter
from percy.ingest.records import (AreaRecord, CompetitionRecord, MatchRecord, SeasonBundle,
                                  SeasonRecord, TeamRecord)


def _date(value: str | None) -> date | None:
    return date.fromisoformat(value[:10]) if value else None


def _datetime(value: str | None) -> datetime | None:
    """Parse an ISO-8601 UTC timestamp into a naive UTC datetime."""
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)


class FootballDataParser:
    """Maps football-data.org v4 JSON documents to provider-neutral records."""

    def area(self, data: dict | None) -> AreaRecord | None:
        if not data or data.get("id") is None:
            return None
        return AreaRecord(id=data["id"], name=data.get("name", ""), code=data.get("code"), flag=data.get("flag"))

    def season(self, data: dict, competition_id: int) -> SeasonRecord:
        winner = data.get("winner") or {}
        return SeasonRecord(
            id=data["id"],
            competition_id=competition_id,
            start_year=int(data["startDate"][:4]),
            start_date=_date(data.get("startDate")),
            end_date=_date(data.get("endDate")),
            winner_team_id=winner.get("id"),
        )

    def competition(self, data: dict) -> CompetitionRecord:
        seasons = tuple(self.season(s, data["id"]) for s in data.get("seasons", []))
        return CompetitionRecord(
            id=data["id"], name=data["name"], code=data.get("code"), type=data.get("type"),
            emblem=data.get("emblem"), area=self.area(data.get("area")), seasons=seasons,
        )

    def team(self, data: dict) -> TeamRecord:
        return TeamRecord(
            id=data["id"], name=data["name"], short_name=data.get("shortName"), tla=data.get("tla"),
            crest=data.get("crest"), founded=data.get("founded"), venue=data.get("venue"),
            club_colors=data.get("clubColors"), website=data.get("website"), area=self.area(data.get("area")),
        )

    def match(self, data: dict, competition_id: int, season_id: int) -> MatchRecord:
        score = data.get("score") or {}
        full, half = score.get("fullTime") or {}, score.get("halfTime") or {}
        referee = next((r.get("name") for r in data.get("referees", []) if r.get("type") == "REFEREE"), None)
        return MatchRecord(
            id=data["id"],
            competition_id=(data.get("competition") or {}).get("id", competition_id),
            season_id=(data.get("season") or {}).get("id", season_id),
            utc_date=_datetime(data["utcDate"]),
            status=data["status"],
            matchday=data.get("matchday"),
            stage=data.get("stage"),
            home_team_id=data["homeTeam"]["id"],
            away_team_id=data["awayTeam"]["id"],
            winner=score.get("winner"),
            duration=score.get("duration"),
            ft_home=full.get("home"),
            ft_away=full.get("away"),
            ht_home=half.get("home"),
            ht_away=half.get("away"),
            referee=referee,
            last_updated=_datetime(data.get("lastUpdated")),
        )


class FootballDataOrgProvider(FootballDataProvider):
    """Fetches competition, team and match data from football-data.org v4."""

    def __init__(self, client: JsonClient, parser: FootballDataParser | None = None) -> None:
        self.client = client
        self.parser = parser or FootballDataParser()

    @classmethod
    def build(cls, api_key: str, base_url: str, requests_per_minute: int, cache=None) -> "FootballDataOrgProvider":
        """Wire up an HTTP client, optionally wrapped by a cache decorator factory."""
        client: JsonClient = HttpJsonClient(base_url, {"X-Auth-Token": api_key}, RateLimiter(requests_per_minute))
        return cls(cache(client) if cache else client)

    def competition(self, code: str) -> CompetitionRecord:
        return self.parser.competition(self.client.get(f"competitions/{code}"))

    def season(self, competition: CompetitionRecord, start_year: int, refresh: bool = False) -> SeasonBundle:
        params = {"season": start_year}
        teams_doc = self.client.get(f"competitions/{competition.code}/teams", params, refresh=refresh)
        matches_doc = self.client.get(f"competitions/{competition.code}/matches", params, refresh=refresh)
        season = self._resolve_season(competition, start_year, teams_doc, matches_doc)
        teams = tuple(self.parser.team(t) for t in teams_doc.get("teams", []))
        matches = tuple(self.parser.match(m, competition.id, season.id) for m in matches_doc.get("matches", []))
        return SeasonBundle(season=season, teams=teams, matches=matches)

    def _resolve_season(self, competition: CompetitionRecord, start_year: int, *docs: dict) -> SeasonRecord:
        """Prefer the season embedded in the responses; fall back to the competition's season list."""
        for doc in docs:
            if doc.get("season"):
                return self.parser.season(doc["season"], competition.id)
            for m in doc.get("matches", []):
                if m.get("season"):
                    return self.parser.season(m["season"], competition.id)
        for s in competition.seasons:
            if s.start_year == start_year:
                return s
        raise ValueError(f"season {start_year} not found for {competition.code}")
