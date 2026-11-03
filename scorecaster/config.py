"""Application settings loaded from environment variables and an optional .env file."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, model_validator

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FIRST_SEASON = 2005


def current_season_start(today: date | None = None) -> int:
    """Return the start year of the August–May season in progress: 2026-11-02 -> 2026, 2027-03-01 -> 2026."""
    today = today or date.today()
    return today.year if today.month >= 7 else today.year - 1


def load_dotenv(path: Path) -> None:
    """Populate os.environ from a simple KEY=VALUE file without overriding existing values."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


@dataclass(frozen=True)
class FeatureConfig:
    """Tunable parameters for the pre-match feature builder."""

    form_windows: tuple[int, ...] = (4, 6, 8)
    goal_windows: tuple[int, ...] = (4, 6, 8, 10, 20)
    venue_windows: tuple[int, ...] = (4, 6, 8)
    position_bands: tuple[tuple[int, int], ...] = ((1, 4), (5, 8), (9, 12), (13, 16), (17, 20))
    relegation_places: int = 3
    h2h_last_n: int = 6
    h2h_venue_last_n: int = 3
    similar_opponent_last_n: int = 10
    min_games_for_strength: int = 3
    elo_initial: float = 1500.0
    elo_k: float = 20.0
    elo_home_advantage: float = 60.0
    elo_season_regression: float = 0.2


class LeagueConfig(BaseModel, frozen=True):
    """One football-data.co.uk league: per-season files (`season`) or one file of every season (`all_seasons`)."""

    code: str = Field(min_length=1, max_length=10)
    country: str
    name: str
    tier: int = Field(ge=1)
    file_style: Literal["season", "all_seasons"]
    first_season: int | None = None

    @model_validator(mode="after")
    def check_first_season(self) -> "LeagueConfig":
        """Require a first season for per-season files, no later than the season in progress."""
        if self.file_style == "season":
            if self.first_season is None:
                raise ValueError(f"{self.code}: per-season leagues need first_season")
            if self.first_season > current_season_start():
                raise ValueError(f"{self.code}: first_season {self.first_season} is in the future")
        return self


def _main(code: str, country: str, name: str, tier: int) -> LeagueConfig:
    return LeagueConfig(code=code, country=country, name=name, tier=tier, file_style="season",
                        first_season=FIRST_SEASON)


def _extra(code: str, country: str, name: str) -> LeagueConfig:
    return LeagueConfig(code=code, country=country, name=name, tier=1, file_style="all_seasons")


LEAGUES: tuple[LeagueConfig, ...] = (
    _main("E0", "England", "Premier League", 1),
    _main("E1", "England", "Championship", 2),
    _main("E2", "England", "League One", 3),
    _main("E3", "England", "League Two", 4),
    _main("EC", "England", "National League", 5),
    _main("SC0", "Scotland", "Premiership", 1),
    _main("SC1", "Scotland", "Championship", 2),
    _main("SC2", "Scotland", "League One", 3),
    _main("SC3", "Scotland", "League Two", 4),
    _main("D1", "Germany", "Bundesliga", 1),
    _main("D2", "Germany", "2. Bundesliga", 2),
    _main("I1", "Italy", "Serie A", 1),
    _main("I2", "Italy", "Serie B", 2),
    _main("SP1", "Spain", "La Liga", 1),
    _main("SP2", "Spain", "Segunda División", 2),
    _main("F1", "France", "Ligue 1", 1),
    _main("F2", "France", "Ligue 2", 2),
    _main("N1", "Netherlands", "Eredivisie", 1),
    _main("B1", "Belgium", "Pro League", 1),
    _main("P1", "Portugal", "Primeira Liga", 1),
    _main("T1", "Turkey", "Süper Lig", 1),
    _main("G1", "Greece", "Super League", 1),
    _extra("ARG", "Argentina", "Liga Profesional"),
    _extra("AUT", "Austria", "Bundesliga"),
    _extra("BRA", "Brazil", "Série A"),
    _extra("DNK", "Denmark", "Superliga"),
    _extra("FIN", "Finland", "Veikkausliiga"),
    _extra("IRL", "Ireland", "Premier Division"),
    _extra("JPN", "Japan", "J1 League"),
    _extra("MEX", "Mexico", "Liga MX"),
    _extra("NOR", "Norway", "Eliteserien"),
    _extra("POL", "Poland", "Ekstraklasa"),
    _extra("ROU", "Romania", "Liga I"),
    _extra("SWE", "Sweden", "Allsvenskan"),
    _extra("SWZ", "Switzerland", "Super League"),
    _extra("USA", "USA", "MLS"),
)


@dataclass(frozen=True)
class Settings:
    """Runtime settings for storage and feature building."""

    db_path: Path = PROJECT_ROOT / "data" / "scorecaster.db"
    features: FeatureConfig = field(default_factory=FeatureConfig)

    @property
    def db_url(self) -> str:
        """SQLAlchemy URL for the SQLite database."""
        return f"sqlite:///{self.db_path}"

    @classmethod
    def from_env(cls, env_file: Path | None = PROJECT_ROOT / ".env") -> "Settings":
        """Build settings from the environment, reading the .env file first."""
        if env_file is not None:
            load_dotenv(env_file)
        return cls(
            db_path=Path(os.environ.get("SCORECASTER_DB_PATH", PROJECT_ROOT / "data" / "scorecaster.db")),
        )
