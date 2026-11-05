"""List the leagues to load from football-data.co.uk, and their seasons."""
from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, model_validator

FIRST_SEASON = 2005


def current_season_start(today: date | None = None) -> int:
    """Return the start year of the August–May season in progress.

    2026-11-02 -> 2026; 2027-03-01 -> 2026
    """
    today = today or date.today()
    return today.year if today.month >= 7 else today.year - 1


class LeagueConfig(BaseModel, frozen=True):
    """One league on the site and how its files are laid out.

    Main leagues have one file per season (`season`), from `first_season`
    on. Extra leagues have one file holding every season (`all_seasons`).
    `calendar_year` marks leagues whose seasons run January to December;
    the rest run August to May.
    """

    code: str = Field(min_length=1, max_length=10)
    country: str
    name: str
    tier: int = Field(ge=1)
    file_style: Literal["season", "all_seasons"]
    first_season: int | None = None
    calendar_year: bool = False

    @model_validator(mode="after")
    def check_first_season(self) -> LeagueConfig:
        """Require a past or current first season for per-season leagues."""
        if self.file_style != "season":
            return self
        code, first = self.code, self.first_season
        if first is None:
            raise ValueError(f"{code}: per-season leagues need first_season")
        if first > current_season_start():
            raise ValueError(f"{code}: first_season {first} is in the future")
        return self


def _main_league(
    code: str, country: str, name: str, tier: int
) -> LeagueConfig:
    """Return a main league, loaded one season file at a time."""
    return LeagueConfig(
        code=code,
        country=country,
        name=name,
        tier=tier,
        file_style="season",
        first_season=FIRST_SEASON,
    )


def _extra_league(
    code: str, country: str, name: str, calendar_year: bool = False
) -> LeagueConfig:
    """Return an extra league, loaded from one file of every season."""
    return LeagueConfig(
        code=code,
        country=country,
        name=name,
        tier=1,
        file_style="all_seasons",
        calendar_year=calendar_year,
    )


LEAGUES: tuple[LeagueConfig, ...] = (
    _main_league("E0", "England", "Premier League", 1),
    _main_league("E1", "England", "Championship", 2),
    _main_league("E2", "England", "League One", 3),
    _main_league("E3", "England", "League Two", 4),
    _main_league("EC", "England", "National League", 5),
    _main_league("SC0", "Scotland", "Premiership", 1),
    _main_league("SC1", "Scotland", "Championship", 2),
    _main_league("SC2", "Scotland", "League One", 3),
    _main_league("SC3", "Scotland", "League Two", 4),
    _main_league("D1", "Germany", "Bundesliga", 1),
    _main_league("D2", "Germany", "2. Bundesliga", 2),
    _main_league("I1", "Italy", "Serie A", 1),
    _main_league("I2", "Italy", "Serie B", 2),
    _main_league("SP1", "Spain", "La Liga", 1),
    _main_league("SP2", "Spain", "Segunda División", 2),
    _main_league("F1", "France", "Ligue 1", 1),
    _main_league("F2", "France", "Ligue 2", 2),
    _main_league("N1", "Netherlands", "Eredivisie", 1),
    _main_league("B1", "Belgium", "Pro League", 1),
    _main_league("P1", "Portugal", "Primeira Liga", 1),
    _main_league("T1", "Turkey", "Süper Lig", 1),
    _main_league("G1", "Greece", "Super League", 1),
    _extra_league("ARG", "Argentina", "Liga Profesional", calendar_year=True),
    _extra_league("AUT", "Austria", "Bundesliga"),
    _extra_league("BRA", "Brazil", "Série A", calendar_year=True),
    _extra_league("DNK", "Denmark", "Superliga"),
    _extra_league("FIN", "Finland", "Veikkausliiga", calendar_year=True),
    _extra_league("IRL", "Ireland", "Premier Division", calendar_year=True),
    _extra_league("JPN", "Japan", "J1 League"),
    _extra_league("MEX", "Mexico", "Liga MX"),
    _extra_league("NOR", "Norway", "Eliteserien", calendar_year=True),
    _extra_league("POL", "Poland", "Ekstraklasa"),
    _extra_league("ROU", "Romania", "Liga I"),
    _extra_league("SWE", "Sweden", "Allsvenskan", calendar_year=True),
    _extra_league("SWZ", "Switzerland", "Super League"),
    _extra_league("USA", "USA", "MLS", calendar_year=True),
)
