"""Parse football-data.co.uk CSVs into seasons, teams and matches."""
from __future__ import annotations

import io
import logging

import pandas as pd
from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from scorecaster.db import Competition, Database, Match, Season, Team, TeamAlias
from scorecaster.ingest.download import CsvFile

log = logging.getLogger(__name__)

OLD_NAMES = {"HG": "FTHG", "AG": "FTAG", "Res": "FTR"}
REQUIRED_COLUMNS = ["Date", "HomeTeam", "AwayTeam"]
NUMBER_COLUMNS = {
    "FTHG": "ft_home", "FTAG": "ft_away", "HTHG": "ht_home", "HTAG": "ht_away",
    "HS": "home_shots", "AS": "away_shots", "HST": "home_shots_on_target", "AST": "away_shots_on_target",
    "HF": "home_fouls", "AF": "away_fouls", "HC": "home_corners", "AC": "away_corners",
    "HY": "home_yellows", "AY": "away_yellows", "HR": "home_reds", "AR": "away_reds",
}
TEXT_COLUMNS = {"FTR": "ft_result", "HTR": "ht_result", "Referee": "referee"}
MATCH_KEY = ["competition_id", "match_date", "home_team_id", "away_team_id"]


def decode_csv(body: bytes) -> str:
    """Decode a CSV body as UTF-8 (dropping any BOM), falling back to cp1252 for older files."""
    try:
        return body.decode("utf-8-sig")
    except UnicodeDecodeError:
        return body.decode("cp1252")


def parse_dates(raw: pd.Series) -> pd.Series:
    """Parse dd/mm/yy and dd/mm/yyyy dates in one column: '10/08/24' and '10/08/2024' -> 2024-08-10."""
    text = raw.astype(str).str.strip()
    long_dates = pd.to_datetime(text.where(text.str.len() == 10), format="%d/%m/%Y", errors="coerce")
    short_dates = pd.to_datetime(text.where(text.str.len() == 8), format="%d/%m/%y", errors="coerce")
    return long_dates.fillna(short_dates).dt.date


def to_numbers(results_df: pd.DataFrame, columns: list[str], label: str) -> None:
    """Convert columns to numbers in place, logging every non-empty value that fails to convert."""
    for col in columns:
        converted = pd.to_numeric(results_df[col], errors="coerce")
        failed = results_df[col].notna() & converted.isna()
        for idx, value in results_df.loc[failed, col].items():
            log.warning("%s row %s: %s=%r is not a number", label, idx, col, value)
        results_df[col] = converted


def read_results(body: bytes, label: str) -> pd.DataFrame:
    """Read a main-league CSV into one row per match with dates parsed and numbers converted."""
    text = decode_csv(body)
    width = len(text.splitlines()[0].split(","))

    def trim_extra_fields(fields: list[str]) -> list[str] | None:
        """Drop empty fields beyond the header width; skip the row when the extras hold data."""
        if all(not f.strip() for f in fields[width:]):
            return fields[:width]
        log.warning("%s: dropped row with extra data: %s", label, ",".join(fields))
        return None

    results_df = pd.read_csv(io.StringIO(text), dtype=str, engine="python", on_bad_lines=trim_extra_fields)
    results_df = results_df.loc[:, ~results_df.columns.str.startswith("Unnamed")]
    results_df = results_df.rename(columns=OLD_NAMES).dropna(subset=REQUIRED_COLUMNS)
    results_df["Date"] = parse_dates(results_df["Date"])
    bad_dates = results_df["Date"].isna()
    for idx in results_df.index[bad_dates]:
        log.warning("%s row %s: unreadable date", label, idx)
    results_df = results_df[~bad_dates].copy()
    if "Time" in results_df:
        results_df["Time"] = pd.to_datetime(results_df["Time"], format="%H:%M", errors="coerce").dt.time
    to_numbers(results_df, [c for c in NUMBER_COLUMNS if c in results_df], label)
    return results_df


def season_label(start_year: int) -> str:
    """Return the label for a season starting in `start_year`: 2024 -> '2024/25'."""
    return f"{start_year}/{(start_year + 1) % 100:02d}"


class TeamResolver:
    """Map (country, name) to a team id via aliases, then teams, inserting unknown names as new teams."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.ids: dict[tuple[str, str], int] = {
            (t.country, t.name): t.id for t in session.scalars(select(Team))}
        self.ids.update({(a.country, a.alias): a.team_id for a in session.scalars(select(TeamAlias))})

    def resolve(self, country: str, name: str) -> int:
        """Return the team id for a name: ('England', 'Middlesboro') -> id of Middlesbrough when aliased."""
        key = (country, name.strip())
        if key not in self.ids:
            team = Team(country=key[0], name=key[1])
            self.session.add(team)
            self.session.flush()
            self.ids[key] = team.id
        return self.ids[key]


class MainLeagueLoader:
    """Load a main-league season CSV into seasons, teams and matches, updating rows that already exist."""

    def __init__(self, db: Database, current_season: int) -> None:
        self.db = db
        self.current_season = current_season

    def load(self, csv_file: CsvFile, body: bytes) -> int:
        """Parse and upsert one league-season file. Returns the number of matches written."""
        league, start = csv_file.league, csv_file.season_start
        label = f"{league.code} {season_label(start)}"
        results_df = read_results(body, label)
        with self.db.session() as s:
            competition_id = s.scalar(select(Competition.id).where(Competition.code == league.code))
            season_id = self._season_id(s, competition_id, start)
            teams = TeamResolver(s)
            unplayed = "scheduled" if start == self.current_season else "void"
            rows = [self._match_row(r, competition_id, season_id, league.country, teams, unplayed)
                    for r in results_df.to_dict("records")]
            if rows:
                stmt = sqlite_insert(Match.__table__)
                stmt = stmt.on_conflict_do_update(
                    index_elements=MATCH_KEY,
                    set_={c: stmt.excluded[c] for c in rows[0] if c not in MATCH_KEY},
                )
                s.connection().execute(stmt, rows)
        missing = [c for c in [*NUMBER_COLUMNS, *TEXT_COLUMNS] if c not in results_df]
        log.info("%s: %d matches%s", label, len(rows), f"; no {', '.join(missing)}" if missing else "")
        return len(rows)

    @staticmethod
    def _season_id(s: Session, competition_id: int, start: int) -> int:
        label = season_label(start)
        season = s.scalar(select(Season).where(Season.competition_id == competition_id, Season.label == label))
        if season is None:
            season = Season(competition_id=competition_id, label=label, start_year=start, end_year=start + 1)
            s.add(season)
            s.flush()
        return season.id

    @staticmethod
    def _match_row(r: dict, competition_id: int, season_id: int, country: str, teams: TeamResolver,
                   unplayed: str) -> dict:
        row = {
            "competition_id": competition_id, "season_id": season_id, "match_date": r["Date"],
            "kickoff_time": r.get("Time") if pd.notna(r.get("Time")) else None,
            "home_team_id": teams.resolve(country, r["HomeTeam"]),
            "away_team_id": teams.resolve(country, r["AwayTeam"]),
        }
        for src, dest in NUMBER_COLUMNS.items():
            value = r.get(src)
            row[dest] = int(value) if pd.notna(value) else None
        for src, dest in TEXT_COLUMNS.items():
            value = r.get(src)
            row[dest] = value.strip() if isinstance(value, str) and value.strip() else None
        row["status"] = "finished" if row["ft_home"] is not None and row["ft_away"] is not None else unplayed
        return row
