"""ORM models for the football-data.co.uk tables."""
from __future__ import annotations

from datetime import date, datetime, time

from sqlalchemy import (
    Date, 
    DateTime, 
    Float, 
    ForeignKey, 
    Integer, 
    LargeBinary, 
    String, 
    Time,
    UniqueConstraint
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base shared by all models."""


class Competition(Base):
    __tablename__ = "competitions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(10), unique=True)
    country: Mapped[str] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(String(100))
    tier: Mapped[int] = mapped_column(Integer)


class Season(Base):
    __tablename__ = "seasons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    competition_id: Mapped[int] = mapped_column(ForeignKey("competitions.id"))
    label: Mapped[str] = mapped_column(String(9))
    start_year: Mapped[int] = mapped_column(Integer, index=True)
    end_year: Mapped[int] = mapped_column(Integer)

    __table_args__ = (UniqueConstraint("competition_id", "label"),)


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    country: Mapped[str] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(String(100))

    __table_args__ = (UniqueConstraint("country", "name"),)


class TeamAlias(Base):
    """Alternative spelling of a team name, mapped to the team it belongs to."""

    __tablename__ = "team_aliases"

    country: Mapped[str] = mapped_column(String(50), primary_key=True)
    alias: Mapped[str] = mapped_column(String(100), primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    competition_id: Mapped[int] = mapped_column(ForeignKey("competitions.id"), index=True)
    season_id: Mapped[int] = mapped_column(ForeignKey("seasons.id"), index=True)
    match_date: Mapped[date] = mapped_column(Date, index=True)
    kickoff_time: Mapped[time | None] = mapped_column(Time)
    status: Mapped[str] = mapped_column(String(10), index=True)
    home_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), index=True)
    away_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), index=True)
    ft_home: Mapped[int | None] = mapped_column(Integer)
    ft_away: Mapped[int | None] = mapped_column(Integer)
    ft_result: Mapped[str | None] = mapped_column(String(1))
    ht_home: Mapped[int | None] = mapped_column(Integer)
    ht_away: Mapped[int | None] = mapped_column(Integer)
    ht_result: Mapped[str | None] = mapped_column(String(1))
    referee: Mapped[str | None] = mapped_column(String(100))
    home_shots: Mapped[int | None] = mapped_column(Integer)
    away_shots: Mapped[int | None] = mapped_column(Integer)
    home_shots_on_target: Mapped[int | None] = mapped_column(Integer)
    away_shots_on_target: Mapped[int | None] = mapped_column(Integer)
    home_fouls: Mapped[int | None] = mapped_column(Integer)
    away_fouls: Mapped[int | None] = mapped_column(Integer)
    home_corners: Mapped[int | None] = mapped_column(Integer)
    away_corners: Mapped[int | None] = mapped_column(Integer)
    home_yellows: Mapped[int | None] = mapped_column(Integer)
    away_yellows: Mapped[int | None] = mapped_column(Integer)
    home_reds: Mapped[int | None] = mapped_column(Integer)
    away_reds: Mapped[int | None] = mapped_column(Integer)

    __table_args__ = (UniqueConstraint("competition_id", "match_date", "home_team_id", "away_team_id"),)

    @property
    def is_finished(self) -> bool:
        """True when the match has a final score."""
        return self.status == "finished" and self.ft_home is not None and self.ft_away is not None


class Download(Base):
    """Raw CSV cache so files can be re-parsed without new requests."""

    __tablename__ = "downloads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    url: Mapped[str] = mapped_column(String(255), unique=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime)
    body: Mapped[bytes] = mapped_column(LargeBinary)


class Odds(Base):
    """One price: bookmaker, market, selection, line and timing for a match. `line` is 0 for 1X2."""

    __tablename__ = "odds"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id"), index=True)
    bookmaker: Mapped[str] = mapped_column(String(30))
    market: Mapped[str] = mapped_column(String(5))
    selection: Mapped[str] = mapped_column(String(5))
    line: Mapped[float] = mapped_column(Float)
    timing: Mapped[str] = mapped_column(String(10))
    price: Mapped[float] = mapped_column(Float)

    __table_args__ = (UniqueConstraint("match_id", "bookmaker", "market", "selection", "line", "timing"),)
