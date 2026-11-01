"""ORM models for the raw football-data tables."""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Declarative base shared by all models."""


class Area(Base):
    __tablename__ = "areas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    code: Mapped[str | None] = mapped_column(String(10))
    flag: Mapped[str | None] = mapped_column(String(255))


class Competition(Base):
    __tablename__ = "competitions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    area_id: Mapped[int | None] = mapped_column(ForeignKey("areas.id"))
    name: Mapped[str] = mapped_column(String(100))
    code: Mapped[str | None] = mapped_column(String(10), unique=True)
    type: Mapped[str | None] = mapped_column(String(20))
    emblem: Mapped[str | None] = mapped_column(String(255))

    area: Mapped[Area | None] = relationship()


class Season(Base):
    __tablename__ = "seasons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    competition_id: Mapped[int] = mapped_column(ForeignKey("competitions.id"))
    start_year: Mapped[int] = mapped_column(Integer, index=True)
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    winner_team_id: Mapped[int | None] = mapped_column(Integer)

    __table_args__ = (UniqueConstraint("competition_id", "start_year"),)


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    area_id: Mapped[int | None] = mapped_column(ForeignKey("areas.id"))
    name: Mapped[str] = mapped_column(String(100))
    short_name: Mapped[str | None] = mapped_column(String(50))
    tla: Mapped[str | None] = mapped_column(String(5))
    crest: Mapped[str | None] = mapped_column(String(255))
    founded: Mapped[int | None] = mapped_column(Integer)
    venue: Mapped[str | None] = mapped_column(String(100))
    club_colors: Mapped[str | None] = mapped_column(String(100))
    website: Mapped[str | None] = mapped_column(String(255))


class SeasonTeam(Base):
    """Which teams took part in which season."""

    __tablename__ = "season_teams"

    season_id: Mapped[int] = mapped_column(ForeignKey("seasons.id"), primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), primary_key=True)


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    competition_id: Mapped[int] = mapped_column(ForeignKey("competitions.id"), index=True)
    season_id: Mapped[int] = mapped_column(ForeignKey("seasons.id"), index=True)
    utc_date: Mapped[datetime] = mapped_column(DateTime, index=True)
    status: Mapped[str] = mapped_column(String(20), index=True)
    matchday: Mapped[int | None] = mapped_column(Integer)
    stage: Mapped[str | None] = mapped_column(String(30))
    home_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), index=True)
    away_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), index=True)
    winner: Mapped[str | None] = mapped_column(String(10))
    duration: Mapped[str | None] = mapped_column(String(20))
    ft_home: Mapped[int | None] = mapped_column(Integer)
    ft_away: Mapped[int | None] = mapped_column(Integer)
    ht_home: Mapped[int | None] = mapped_column(Integer)
    ht_away: Mapped[int | None] = mapped_column(Integer)
    referee: Mapped[str | None] = mapped_column(String(100))
    last_updated: Mapped[datetime | None] = mapped_column(DateTime)

    @property
    def is_finished(self) -> bool:
        """True when the match has a final score."""
        return self.status == "FINISHED" and self.ft_home is not None and self.ft_away is not None


class ApiResponse(Base):
    """Raw API response cache so data can be re-parsed without new requests."""

    __tablename__ = "api_responses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    path: Mapped[str] = mapped_column(String(255))
    params: Mapped[str] = mapped_column(String(255), default="")
    fetched_at: Mapped[datetime] = mapped_column(DateTime)
    body: Mapped[str] = mapped_column(Text)

    __table_args__ = (UniqueConstraint("path", "params"),)
