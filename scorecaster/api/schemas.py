"""Pydantic models for the API's JSON responses."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class CompetitionResponse(BaseModel):
    """A competition in the app.

    e.g. {"code": "E0", "name": "Premier League", "country": "England",
    "tier": 1}
    """

    model_config = ConfigDict(from_attributes=True)

    code: str
    name: str
    country: str
    tier: int


class SeasonResponse(BaseModel):
    """A season of a competition.

    e.g. {"label": "2024/25", "start_year": 2024, "end_year": 2025}
    """

    model_config = ConfigDict(from_attributes=True)

    label: str
    start_year: int
    end_year: int
