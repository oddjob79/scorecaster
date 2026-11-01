"""Abstractions for API transport and data providers."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from scorecaster.ingest.records import CompetitionRecord, SeasonBundle


class ApiError(RuntimeError):
    """Raised when an API request fails."""

    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(f"HTTP {status_code}: {message}")
        self.status_code = status_code


class JsonClient(ABC):
    """Fetches a JSON document for a path and query parameters."""

    @abstractmethod
    def get(self, path: str, params: dict[str, Any] | None = None, refresh: bool = False) -> dict:
        """Return the decoded JSON body; `refresh` bypasses any cache."""


class FootballDataProvider(ABC):
    """Source of competitions, teams and matches, independent of the concrete API."""

    @abstractmethod
    def competition(self, code: str) -> CompetitionRecord:
        """Competition metadata, including its area and known seasons."""

    @abstractmethod
    def season(self, competition: CompetitionRecord, start_year: int, refresh: bool = False) -> SeasonBundle:
        """Teams and matches for one season of a competition."""
