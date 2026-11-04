"""Load runtime settings from the environment and an optional .env file."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "scorecaster.db"


def load_dotenv(path: Path) -> None:
    """Copy KEY=VALUE lines from a file into os.environ.

    Values already in the environment win, so a shell variable overrides
    the file. Blank lines and lines starting with # are ignored.
    """
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key.strip(), value)


@dataclass(frozen=True)
class FeatureConfig:
    """Tunable parameters for the pre-match feature builder."""

    form_windows: tuple[int, ...] = (4, 6, 8)
    goal_windows: tuple[int, ...] = (4, 6, 8, 10, 20)
    venue_windows: tuple[int, ...] = (4, 6, 8)
    position_bands: tuple[tuple[int, int], ...] = (
        (1, 4),
        (5, 8),
        (9, 12),
        (13, 16),
        (17, 20),
    )
    relegation_places: int = 3
    h2h_last_n: int = 6
    h2h_venue_last_n: int = 3
    similar_opponent_last_n: int = 10
    min_games_for_strength: int = 3
    elo_initial: float = 1500.0
    elo_k: float = 20.0
    elo_home_advantage: float = 60.0
    elo_season_regression: float = 0.2


@dataclass(frozen=True)
class Settings:
    """Runtime settings for storage and feature building."""

    db_path: Path = DEFAULT_DB_PATH
    features: FeatureConfig = field(default_factory=FeatureConfig)

    @property
    def db_url(self) -> str:
        """Return the SQLAlchemy URL for the SQLite database."""
        return f"sqlite:///{self.db_path}"

    @classmethod
    def from_env(
        cls, env_file: Path | None = PROJECT_ROOT / ".env"
    ) -> Settings:
        """Build settings from the environment, reading the .env file first.

        SCORECASTER_DB_PATH points the database somewhere other than
        data/scorecaster.db.
        """
        if env_file is not None:
            load_dotenv(env_file)
        db_path = os.environ.get("SCORECASTER_DB_PATH", DEFAULT_DB_PATH)
        return cls(db_path=Path(db_path))
