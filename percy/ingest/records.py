"""Provider-neutral records passed from API providers to repositories."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class AreaRecord:
    id: int
    name: str
    code: str | None = None
    flag: str | None = None


@dataclass(frozen=True)
class SeasonRecord:
    id: int
    competition_id: int
    start_year: int
    start_date: date | None = None
    end_date: date | None = None
    winner_team_id: int | None = None


@dataclass(frozen=True)
class CompetitionRecord:
    id: int
    name: str
    code: str | None
    type: str | None
    emblem: str | None
    area: AreaRecord | None
    seasons: tuple[SeasonRecord, ...] = ()


@dataclass(frozen=True)
class TeamRecord:
    id: int
    name: str
    short_name: str | None = None
    tla: str | None = None
    crest: str | None = None
    founded: int | None = None
    venue: str | None = None
    club_colors: str | None = None
    website: str | None = None
    area: AreaRecord | None = None


@dataclass(frozen=True)
class MatchRecord:
    id: int
    competition_id: int
    season_id: int
    utc_date: datetime
    status: str
    home_team_id: int
    away_team_id: int
    matchday: int | None = None
    stage: str | None = None
    winner: str | None = None
    duration: str | None = None
    ft_home: int | None = None
    ft_away: int | None = None
    ht_home: int | None = None
    ht_away: int | None = None
    referee: str | None = None
    last_updated: datetime | None = None


@dataclass(frozen=True)
class SeasonBundle:
    """Everything fetched for one competition season."""

    season: SeasonRecord
    teams: tuple[TeamRecord, ...]
    matches: tuple[MatchRecord, ...]
