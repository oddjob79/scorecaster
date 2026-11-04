"""Write parsed football-data.co.uk files to the database."""
from __future__ import annotations

import logging
from datetime import date

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from scorecaster.db import (
    Competition,
    Database,
    Match,
    Odds,
    Season,
    Team,
    TeamAlias,
    upsert,
)
from scorecaster.ingest.fdcuk.columns import (
    NUMBER_COLUMNS,
    TEXT_COLUMNS,
    unknown_columns,
)
from scorecaster.ingest.fdcuk.files import CsvFile
from scorecaster.ingest.fdcuk.odds import build_odds_rows
from scorecaster.ingest.fdcuk.reader import read_results
from scorecaster.ingest.fdcuk.seasons import SeasonSpan
from scorecaster.leagues import LeagueConfig

log = logging.getLogger(__name__)

MATCH_KEY = ["competition_id", "match_date", "home_team_id", "away_team_id"]
ODDS_KEY = ["match_id", "bookmaker", "market", "selection", "line", "timing"]


class CsvLoader:
    """Load football-data.co.uk files into seasons, teams, matches and odds.

    Loading is an upsert: re-loading a file updates rows in place, so a
    season in progress can be re-read as results arrive.
    """

    def __init__(
        self,
        db: Database,
        current_season: int,
        current_year: int | None = None,
    ) -> None:
        self.db = db
        self.current_season = current_season
        self.current_year = current_year or date.today().year

    def load(self, csv_file: CsvFile, body: bytes) -> int:
        """Load one file: a league-season, or every season of a league.

        Returns the number of matches written.
        """
        label = _file_label(csv_file)
        results_df = read_results(body, label)
        unknown = unknown_columns(list(results_df.columns))
        if unknown:
            log.warning("%s: unknown columns %s", label, ", ".join(unknown))
        return sum(
            self._load_season(csv_file.league, season, season_df)
            for season, season_df in _split_seasons(csv_file, results_df)
        )

    def _load_season(
        self,
        league: LeagueConfig,
        season: SeasonSpan,
        season_df: pd.DataFrame,
    ) -> int:
        """Write one season's matches and odds in a single transaction."""
        label = f"{league.code} {season.label}"
        unplayed_status = self._unplayed_status(season)
        with self.db.session() as session:
            writer = SeasonWriter(session, league, season, unplayed_status)
            match_count, odds_count = writer.write(season_df, label)
        _log_season(label, season_df, match_count, odds_count)
        return match_count

    def _unplayed_status(self, season: SeasonSpan) -> str:
        """Return the status for a match without a score.

        'scheduled' in the season in progress, 'void' in any earlier one.
        """
        if season.is_calendar_year:
            current_start = self.current_year
        else:
            current_start = self.current_season
        return "scheduled" if season.start == current_start else "void"


class SeasonWriter:
    """Write one league-season's matches and odds within an open session."""

    def __init__(
        self,
        session: Session,
        league: LeagueConfig,
        season: SeasonSpan,
        unplayed_status: str,
    ) -> None:
        self.session = session
        self.country = league.country
        self.unplayed_status = unplayed_status
        self.competition_id = session.scalar(
            select(Competition.id).where(Competition.code == league.code)
        )
        self.season_id = self._find_or_create_season(season)
        self.teams = TeamResolver(session)

    def write(self, season_df: pd.DataFrame, label: str) -> tuple[int, int]:
        """Upsert the season's matches, then their odds.

        Returns the number of (matches, odds) written.
        """
        records = season_df.to_dict("records")
        match_rows = [self._match_row(record) for record in records]
        upsert(self.session, Match.__table__, match_rows, MATCH_KEY)
        match_ids = self._match_ids(match_rows)
        odds_rows = build_odds_rows(season_df, match_ids, label)
        upsert(self.session, Odds.__table__, odds_rows, ODDS_KEY)
        return len(match_rows), len(odds_rows)

    def _find_or_create_season(self, season: SeasonSpan) -> int:
        """Return this competition's season id, creating it if new."""
        row = self.session.scalar(
            select(Season).where(
                Season.competition_id == self.competition_id,
                Season.label == season.label,
            )
        )
        if row is None:
            row = Season(
                competition_id=self.competition_id,
                label=season.label,
                start_year=season.start,
                end_year=season.end,
            )
            self.session.add(row)
            self.session.flush()
        return row.id

    def _match_row(self, record: dict) -> dict:
        """Turn one CSV record into a matches-table row."""
        home_team_id = self.teams.resolve(self.country, record["HomeTeam"])
        away_team_id = self.teams.resolve(self.country, record["AwayTeam"])
        row = {
            "competition_id": self.competition_id,
            "season_id": self.season_id,
            "match_date": record["Date"],
            "kickoff_time": _value_or_none(record.get("Time")),
            "home_team_id": home_team_id,
            "away_team_id": away_team_id,
        }
        for source, column in NUMBER_COLUMNS.items():
            row[column] = _int_or_none(record.get(source))
        for source, column in TEXT_COLUMNS.items():
            row[column] = _text_or_none(record.get(source))
        has_score = row["ft_home"] is not None and row["ft_away"] is not None
        row["status"] = "finished" if has_score else self.unplayed_status
        return row

    def _match_ids(self, match_rows: list[dict]) -> list[int]:
        """Return the stored id of each match row, in the same order."""
        stored = self.session.execute(
            select(
                Match.id,
                Match.match_date,
                Match.home_team_id,
                Match.away_team_id,
            ).where(Match.season_id == self.season_id)
        )
        ids = {
            (day, home, away): match_id
            for match_id, day, home, away in stored
        }
        return [
            ids[(row["match_date"], row["home_team_id"], row["away_team_id"])]
            for row in match_rows
        ]


class TeamResolver:
    """Map a team name to its id, creating teams for new names.

    Names are looked up per country, first in ``team_aliases`` (so a
    spelling such as ``Middlesboro`` lands on Middlesbrough), then in
    ``teams``.
    """

    def __init__(self, session: Session) -> None:
        self.session = session
        self.ids = {
            (team.country, team.name): team.id
            for team in session.scalars(select(Team))
        }
        for alias in session.scalars(select(TeamAlias)):
            self.ids[(alias.country, alias.alias)] = alias.team_id

    def resolve(self, country: str, name: str) -> int:
        """Return the team id for `name` in `country`."""
        key = (country, name.strip())
        if key not in self.ids:
            team = Team(country=country, name=key[1])
            self.session.add(team)
            self.session.flush()
            self.ids[key] = team.id
        return self.ids[key]


def _split_seasons(
    csv_file: CsvFile, results_df: pd.DataFrame
) -> list[tuple[SeasonSpan, pd.DataFrame]]:
    """Return each season in the file with its rows.

    A per-season file holds one season; an extra-league file holds all.
    """
    if csv_file.season_start is not None:
        season = SeasonSpan.starting(csv_file.season_start)
        return [(season, results_df)]
    return [
        (SeasonSpan.parse(value), season_df.copy())
        for value, season_df in results_df.groupby("Season", sort=False)
    ]


def _file_label(csv_file: CsvFile) -> str:
    """Name a file in log messages: 'E0 2024/25', or 'BRA'."""
    code = csv_file.league.code
    if csv_file.season_start is None:
        return code
    return f"{code} {SeasonSpan.starting(csv_file.season_start).label}"


def _log_season(
    label: str, season_df: pd.DataFrame, match_count: int, odds_count: int
) -> None:
    """Log a season's counts and the result or stats columns it lacks."""
    expected = [*NUMBER_COLUMNS, *TEXT_COLUMNS]
    missing = [name for name in expected if name not in season_df]
    note = f"; no {', '.join(missing)}" if missing else ""
    log.info("%s: %d matches, %d odds%s", label, match_count, odds_count, note)


def _value_or_none(value: object) -> object | None:
    """Return the value, or None for pandas' empty markers (NaN, NaT)."""
    return value if pd.notna(value) else None


def _int_or_none(value: object) -> int | None:
    """Return a numeric CSV value as an int, or None when it's empty."""
    return int(value) if pd.notna(value) else None


def _text_or_none(value: object) -> str | None:
    """Return trimmed text, or None when the value is empty or blank."""
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None
