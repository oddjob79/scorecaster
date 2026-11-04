"""List the football-data.co.uk CSV files the league config covers."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from scorecaster.leagues import LeagueConfig

BASE_URL = "https://www.football-data.co.uk"


@dataclass(frozen=True)
class CsvFile:
    """One CSV on the site.

    A main league has one file per season (`season_start` set). An extra
    league has one file holding every season (`season_start` is None).
    """

    league: LeagueConfig
    season_start: int | None
    url: str

    def is_live(self, current_season: int) -> bool:
        """Return True when the file can still change.

        That is the season in progress, or any all-seasons file, since it
        includes the season in progress.
        """
        if self.season_start is None:
            return True
        return self.season_start == current_season


def season_dir(start_year: int) -> str:
    """Return the site's folder name for a season: 2024 -> '2425'."""
    return f"{start_year % 100:02d}{(start_year + 1) % 100:02d}"


def list_csv_files(
    leagues: Iterable[LeagueConfig], current_season: int
) -> list[CsvFile]:
    """List every CSV the config covers, oldest season first.

    E0 from 2005 -> mmz4281/0506/E0.csv ... mmz4281/2627/E0.csv;
    BRA -> new/BRA.csv
    """
    files = []
    for league in leagues:
        if league.file_style == "season":
            files.extend(_season_files(league, current_season))
        else:
            files.append(_all_seasons_file(league))
    return files


def _season_files(
    league: LeagueConfig, current_season: int
) -> list[CsvFile]:
    """Return one file per season, from the first season to the current."""
    seasons = range(league.first_season, current_season + 1)
    return [
        CsvFile(league, start, _season_url(league.code, start))
        for start in seasons
    ]


def _all_seasons_file(league: LeagueConfig) -> CsvFile:
    """Return the single file holding every season of an extra league."""
    return CsvFile(league, None, f"{BASE_URL}/new/{league.code}.csv")


def _season_url(code: str, start_year: int) -> str:
    """Return the URL of one league-season file."""
    return f"{BASE_URL}/mmz4281/{season_dir(start_year)}/{code}.csv"
