"""Read the matches and season facts the feature builder replays."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, replace

from sqlalchemy import func, select, text

from scorecaster.db import Competition, Database, Match, Season
from scorecaster.features.market import (
    MarketProbabilities,
    market_probabilities,
)

FEATURE_STATUSES = ("finished", "scheduled")

# Market-average pre-match prices, one row per match. Closing prices are
# set at kick-off, so they would leak into features and aren't read here.
MARKET_PRICES = text("""
    SELECT match_id,
           MAX(CASE WHEN market = '1X2' AND selection = 'home'
               THEN price END) AS home,
           MAX(CASE WHEN market = '1X2' AND selection = 'draw'
               THEN price END) AS draw,
           MAX(CASE WHEN market = '1X2' AND selection = 'away'
               THEN price END) AS away,
           MAX(CASE WHEN market = 'OU' AND selection = 'over'
               THEN price END) AS over,
           MAX(CASE WHEN market = 'OU' AND selection = 'under'
               THEN price END) AS under
    FROM odds
    WHERE bookmaker = 'market_avg' AND timing = 'pre_match'
      AND (market = '1X2' OR (market = 'OU' AND line = 2.5))
    GROUP BY match_id
""")


@dataclass(frozen=True)
class SeasonInfo:
    """One league-season and what the builder needs to know about it.

    `season_games` is how many games each team plays in the season: the
    most any team played, or for the season in progress the previous
    season's figure, since its own isn't known yet.
    """

    id: int
    competition_id: int
    code: str
    country: str
    tier: int
    start_year: int
    team_ids: frozenset[int]
    previous_id: int | None
    season_games: int | None


class MatchSource:
    """Load the matches to replay and the facts about every season."""

    def __init__(self, db: Database) -> None:
        self.db = db

    def matches(self) -> list[Match]:
        """Return finished and scheduled matches in date order."""
        query = (
            select(Match)
            .where(Match.status.in_(FEATURE_STATUSES))
            .order_by(Match.match_date, Match.id)
        )
        with self.db.session() as session:
            return list(session.scalars(query))

    def market(self) -> dict[int, MarketProbabilities]:
        """Return each match's market-average pre-match probabilities."""
        with self.db.engine.connect() as connection:
            rows = connection.execute(MARKET_PRICES)
            return {
                row.match_id: market_probabilities(
                    row.home, row.draw, row.away, row.over, row.under
                )
                for row in rows
            }

    def seasons(self) -> dict[int, SeasonInfo]:
        """Return every season's facts, keyed by season id."""
        with self.db.session() as session:
            rows = session.execute(
                select(
                    Season.id,
                    Season.competition_id,
                    Competition.code,
                    Competition.country,
                    Competition.tier,
                    Season.start_year,
                ).join(Competition, Competition.id == Season.competition_id)
                .order_by(Season.competition_id, Season.start_year)
            ).all()
            teams = self._teams_by_season(session)
            most_games = self._most_games_by_season(session)

        seasons: dict[int, SeasonInfo] = {}
        previous: dict[int, SeasonInfo] = {}
        for row in rows:
            before = previous.get(row.competition_id)
            info = SeasonInfo(
                id=row.id,
                competition_id=row.competition_id,
                code=row.code,
                country=row.country,
                tier=row.tier,
                start_year=row.start_year,
                team_ids=frozenset(teams.get(row.id, ())),
                previous_id=before.id if before else None,
                season_games=most_games.get(row.id),
            )
            seasons[row.id] = info
            previous[row.competition_id] = info
        return _with_current_season_games(seasons, previous)

    @staticmethod
    def _teams_by_season(session) -> dict[int, set[int]]:
        """Return the teams in each season's finished or scheduled matches."""
        teams: dict[int, set[int]] = defaultdict(set)
        rows = session.execute(
            select(Match.season_id, Match.home_team_id, Match.away_team_id)
            .where(Match.status.in_(FEATURE_STATUSES))
        )
        for season_id, home_id, away_id in rows:
            teams[season_id].update((home_id, away_id))
        return teams

    @staticmethod
    def _most_games_by_season(session) -> dict[int, int]:
        """Return the most finished games any team played, per season."""
        games: dict[tuple[int, int], int] = defaultdict(int)
        for column in (Match.home_team_id, Match.away_team_id):
            rows = session.execute(
                select(Match.season_id, column, func.count())
                .where(Match.status == "finished")
                .group_by(Match.season_id, column)
            )
            for season_id, team_id, count in rows:
                games[(season_id, team_id)] += count
        most: dict[int, int] = {}
        for (season_id, _), count in games.items():
            most[season_id] = max(most.get(season_id, 0), count)
        return most


def _with_current_season_games(
    seasons: dict[int, SeasonInfo], latest: dict[int, SeasonInfo]
) -> dict[int, SeasonInfo]:
    """Give each competition's latest season the previous season's length.

    The latest season is the one in progress, so its own game count is
    only the games played so far.
    """
    for season in latest.values():
        before = seasons.get(season.previous_id)
        if before is not None and before.season_games:
            seasons[season.id] = replace(
                season, season_games=before.season_games
            )
    return seasons

