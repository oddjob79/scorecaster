"""Load the site's fixtures files: upcoming matches and their odds."""
from __future__ import annotations

import logging
from datetime import date
from functools import partial

import pandas as pd

from scorecaster.db import Database
from scorecaster.ingest.fdcuk.loader import SeasonWriter
from scorecaster.ingest.fdcuk.reader import read_results
from scorecaster.ingest.fdcuk.seasons import SeasonSpan
from scorecaster.leagues import LEAGUES, LeagueConfig, current_season_start

log = logging.getLogger(__name__)

LEAGUES_BY_CODE = {league.code: league for league in LEAGUES}
EXTRA_LEAGUE_CODES_BY_COUNTRY = {
    league.country: league.code
    for league in LEAGUES
    if league.file_style == "all_seasons"
}


class FixturesLoader:
    """Load upcoming fixtures as scheduled matches with pre-match odds.

    There are two fixtures files: the main leagues' (each row names its
    league in ``Div``) and the extra leagues' (rows give a ``Country``).
    Matches already stored as finished are skipped, so reloading the
    fixtures never overwrites a result.
    """

    def __init__(self, db: Database) -> None:
        self.db = db

    def load(self, body: bytes, label: str) -> int:
        """Load one fixtures file. Returns the number of fixtures written."""
        fixtures_df = read_results(body, label)
        fixtures_df["league_code"] = _league_codes(fixtures_df)
        configured = fixtures_df["league_code"].isin(LEAGUES_BY_CODE)
        if not configured.all():
            log.info(
                "%s: skipped %d fixtures in leagues not configured",
                label,
                (~configured).sum(),
            )
        fixtures_df = fixtures_df[configured]

        written = 0
        for code, league_df in fixtures_df.groupby("league_code"):
            league = LEAGUES_BY_CODE[code]
            seasons = league_df["Date"].map(partial(season_for, league))
            for season, season_df in league_df.groupby(seasons, sort=False):
                written += self._load_season(league, season, season_df)
        return written

    def _load_season(
        self,
        league: LeagueConfig,
        season: SeasonSpan,
        season_df: pd.DataFrame,
    ) -> int:
        """Write one league-season's fixtures, skipping finished matches."""
        label = f"fixtures {league.code} {season.label}"
        with self.db.session() as session:
            writer = SeasonWriter(session, league, season, "scheduled")
            unplayed_df = writer.without_finished(season_df.copy())
            match_count, odds_count = writer.write(unplayed_df, label)
        already_finished = len(season_df) - len(unplayed_df)
        log.info(
            "%s: %d fixtures, %d odds, %d already finished",
            label,
            match_count,
            odds_count,
            already_finished,
        )
        return match_count


def season_for(league: LeagueConfig, day: date) -> SeasonSpan:
    """Return the season a match on `day` belongs to in `league`.

    Calendar-year leagues use the day's year: 2026-11-04 -> 2026.
    August–May leagues use the season started by then: -> 2026/27.
    """
    if league.calendar_year:
        return SeasonSpan(str(day.year), day.year, day.year)
    return SeasonSpan.starting(current_season_start(day))


def _league_codes(fixtures_df: pd.DataFrame) -> pd.Series:
    """Return each row's league code, from ``Div`` or from ``Country``."""
    if "Div" in fixtures_df:
        return fixtures_df["Div"]
    return fixtures_df["Country"].map(EXTRA_LEAGUE_CODES_BY_COUNTRY)
