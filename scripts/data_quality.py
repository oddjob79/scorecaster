"""Report what is wrong or missing in the loaded data.

Prints one section per check, for fixing by hand (e.g. adding team
aliases). The database is opened read-only; nothing is changed.

Re-reading the cached files for unconverted values takes a minute or
two; it runs offline.

    python scripts/data_quality.py
"""
import difflib
import logging
import sqlite3
from datetime import date, timedelta

import pandas as pd

import _bootstrap  # noqa: F401

from scorecaster.config import Settings
from scorecaster.ingest.fdcuk.columns import OddsColumn
from scorecaster.ingest.fdcuk.odds import HANDICAP_LINE_COLUMNS
from scorecaster.ingest.fdcuk.reader import read_results, to_numbers
from scorecaster.leagues import LEAGUES

MID_SEASON_DAYS = 30
PLAYOFF_ONLY_GAMES = 4  # a season this short is a playoff tie, not a season
STALE_GRACE_DAYS = 7
NAME_SIMILARITY = 0.75
MISSING_SHARE = 0.05
# Seasons Pinnacle closing odds cover in full; they stop partway
# through 2025/26 (and calendar 2025).
PINNACLE_SEASONS = range(2012, 2025)

TEAM_SEASONS = """
    SELECT c.code, c.country, s.id AS season_id, s.label, s.start_year,
           t.name AS team, COUNT(*) AS games,
           MIN(side.match_date) AS first_match,
           MAX(side.match_date) AS last_match
    FROM (
        SELECT season_id, competition_id, match_date,
               home_team_id AS team_id
        FROM matches WHERE status = 'finished'
        UNION ALL
        SELECT season_id, competition_id, match_date, away_team_id
        FROM matches WHERE status = 'finished'
    ) AS side
    JOIN competitions c ON c.id = side.competition_id
    JOIN seasons s ON s.id = side.season_id
    JOIN teams t ON t.id = side.team_id
    GROUP BY s.id, t.id
"""
STALE_FIXTURES = """
    SELECT c.code, m.match_date, h.name AS home, a.name AS away
    FROM matches m
    JOIN competitions c ON c.id = m.competition_id
    JOIN teams h ON h.id = m.home_team_id
    JOIN teams a ON a.id = m.away_team_id
    WHERE m.status = 'scheduled' AND m.match_date < ?
    ORDER BY m.match_date
"""
LATEST_SEASONS = """
    SELECT c.code, s.label
    FROM seasons s JOIN competitions c ON c.id = s.competition_id
    WHERE s.start_year = (
        SELECT MAX(start_year) FROM seasons WHERE competition_id = c.id
    )
"""
ODDS_COVERAGE = """
    SELECT c.code, s.label, s.start_year, COUNT(*) AS matches,
           SUM(NOT EXISTS (
               SELECT 1 FROM odds o WHERE o.match_id = m.id
           )) AS no_odds,
           SUM(NOT EXISTS (
               SELECT 1 FROM odds o
               WHERE o.match_id = m.id AND o.bookmaker = 'pinnacle'
                 AND o.market = '1X2' AND o.timing = 'closing'
           )) AS no_pinnacle_closing
    FROM matches m
    JOIN competitions c ON c.id = m.competition_id
    JOIN seasons s ON s.id = m.season_id
    WHERE m.status = 'finished'
    GROUP BY s.id
"""
DUPLICATES = """
    SELECT m.match_date, h.name AS home, a.name AS away,
           GROUP_CONCAT(c.code) AS competitions
    FROM matches m
    JOIN competitions c ON c.id = m.competition_id
    JOIN teams h ON h.id = m.home_team_id
    JOIN teams a ON a.id = m.away_team_id
    GROUP BY m.match_date, m.home_team_id, m.away_team_id
    HAVING COUNT(*) > 1
"""


def main() -> None:
    """Run every check and print its section."""
    db_uri = f"file:{Settings.from_env().db_path}?mode=ro"
    with sqlite3.connect(db_uri, uri=True) as connection:
        team_seasons_df = pd.read_sql_query(TEAM_SEASONS, connection)
        teams_df = pd.read_sql_query(
            "SELECT country, name FROM teams", connection
        )
        report_split_teams(team_seasons_df, teams_df)
        report_stale_fixtures(connection)
        report_season_style(connection)
        report_missing_odds(connection)
        report_duplicates(connection)
        report_unconverted_values(connection)


def report_split_teams(
    team_seasons_df: pd.DataFrame, teams_df: pd.DataFrame
) -> None:
    """Print teams that start or stop mid-season, or appear only once.

    Both can mean one club stored under two spellings. Each flagged team
    gets the most similar names in its country as alias hints, to confirm
    by hand; nothing is merged automatically. Teams that only played a
    playoff tie in a season are listed separately.
    """
    team_seasons_df = team_seasons_df.copy()
    for column in ("first_match", "last_match"):
        team_seasons_df[column] = pd.to_datetime(team_seasons_df[column])
    playoff_only = team_seasons_df["games"] <= PLAYOFF_ONLY_GAMES
    league_df = team_seasons_df[~playoff_only]
    playoff_df = team_seasons_df[playoff_only]

    mid_season_df = _mid_season(league_df)
    seasons_per_team = league_df.groupby(["country", "team"]).size()
    one_season = seasons_per_team[seasons_per_team == 1].index
    names_by_country = teams_df.groupby("country")["name"].apply(list)

    _section(f"Split teams: {len(mid_season_df)} mid-season starts or "
             f"stops, {len(one_season)} one-season teams")
    for row in mid_season_df.itertuples():
        hints = _alias_hints(row.team, names_by_country[row.country])
        print(f"  {row.code} {row.label}: {row.team} "
              f"{row.first_match:%Y-%m-%d} to {row.last_match:%Y-%m-%d}"
              f"{hints}")
    for country, team in one_season:
        hints = _alias_hints(team, names_by_country[country])
        print(f"  one season only: {country} {team}{hints}")

    _section(f"Playoff-only appearances: {len(playoff_df)} (counted as "
             f"league matches)")
    for row in playoff_df.itertuples():
        print(f"  {row.code} {row.label}: {row.team}, {row.games} games "
              f"{row.first_match:%Y-%m-%d} to {row.last_match:%Y-%m-%d}")


def _mid_season(league_df: pd.DataFrame) -> pd.DataFrame:
    """Return team-seasons starting or stopping well away from the norm.

    A season's typical start and end are its median team's first and last
    match, so playoff rounds after the regular season don't stretch it.
    The season in progress isn't checked for early stops.
    """
    typical = league_df.groupby("season_id").agg(
        typical_first=("first_match", "median"),
        typical_last=("last_match", "median"),
    )
    spans_df = league_df.join(typical, on="season_id")
    gap = pd.Timedelta(days=MID_SEASON_DAYS)
    late_start = spans_df["first_match"] > spans_df["typical_first"] + gap
    early_stop = spans_df["last_match"] < spans_df["typical_last"] - gap
    latest = spans_df.groupby("code")["start_year"].transform("max")
    in_progress = spans_df["start_year"] == latest
    return spans_df[late_start | (early_stop & ~in_progress)]


def report_stale_fixtures(connection: sqlite3.Connection) -> None:
    """Print matches still scheduled more than a week after their date.

    These are usually postponed fixtures whose result was loaded under a
    new date, leaving the old row behind. Recent ones are skipped, since
    their results may just not be downloaded yet.
    """
    cutoff = date.today() - timedelta(days=STALE_GRACE_DAYS)
    stale_df = pd.read_sql_query(
        STALE_FIXTURES, connection, params=(cutoff.isoformat(),)
    )
    _section(f"Stale fixtures (over {STALE_GRACE_DAYS} days): "
             f"{len(stale_df)}")
    for row in stale_df.itertuples():
        print(f"  {row.code} {row.match_date}: {row.home} v {row.away}")


def report_season_style(connection: sqlite3.Connection) -> None:
    """Print extra leagues whose latest season doesn't match the config.

    A label like '2026' means January–December, '2026/27' August–May. A
    mismatch means the league has switched calendars, as Japan did.
    """
    latest = dict(connection.execute(LATEST_SEASONS).fetchall())
    mismatches = []
    for league in LEAGUES:
        if league.file_style != "all_seasons" or league.code not in latest:
            continue
        label_is_calendar = "/" not in latest[league.code]
        if label_is_calendar != league.calendar_year:
            mismatches.append((league.code, latest[league.code]))
    _section(f"Season style mismatches: {len(mismatches)}")
    for code, label in mismatches:
        print(f"  {code}: latest season '{label}' doesn't match "
              f"calendar_year in LEAGUES")


def report_missing_odds(connection: sqlite3.Connection) -> None:
    """Print league-seasons where many finished matches lack odds.

    Two shares per league-season: matches with no odds at all, and (for
    the seasons Pinnacle covers) matches without Pinnacle closing 1X2.
    """
    coverage_df = pd.read_sql_query(ODDS_COVERAGE, connection)
    coverage_df["no_odds_share"] = (
        coverage_df["no_odds"] / coverage_df["matches"]
    )
    coverage_df["no_pinnacle_share"] = (
        coverage_df["no_pinnacle_closing"] / coverage_df["matches"]
    )
    in_pinnacle_years = coverage_df["start_year"].isin(PINNACLE_SEASONS)
    flagged_df = coverage_df[
        (coverage_df["no_odds_share"] > MISSING_SHARE)
        | (in_pinnacle_years
           & (coverage_df["no_pinnacle_share"] > MISSING_SHARE))
    ]
    _section(f"Missing odds: {len(flagged_df)} league-seasons over "
             f"{MISSING_SHARE:.0%}")
    for row in flagged_df.itertuples():
        print(f"  {row.code} {row.label}: {row.matches} matches, "
              f"{row.no_odds_share:.0%} no odds, "
              f"{row.no_pinnacle_share:.0%} no Pinnacle closing")


def report_duplicates(connection: sqlite3.Connection) -> None:
    """Print the same fixture stored in more than one competition."""
    duplicates_df = pd.read_sql_query(DUPLICATES, connection)
    _section(f"Duplicate matches: {len(duplicates_df)}")
    for row in duplicates_df.itertuples():
        print(f"  {row.match_date}: {row.home} v {row.away} "
              f"in {row.competitions}")


def report_unconverted_values(connection: sqlite3.Connection) -> None:
    """Re-read every cached CSV and print the values that failed to parse.

    Covers non-numeric results, stats and odds, unreadable dates, and
    rows dropped for holding extra data. Runs offline from the cache.
    """
    capture = _WarningCapture()
    ingest_log = logging.getLogger("scorecaster.ingest.fdcuk")
    ingest_log.addHandler(capture)
    ingest_log.setLevel(logging.WARNING)
    ingest_log.propagate = False  # print once, in this section
    downloads = connection.execute(
        "SELECT url, body FROM downloads WHERE url LIKE '%.csv'"
    ).fetchall()
    for url, body in downloads:
        label = "/".join(url.rsplit("/", 2)[-2:])
        results_df = read_results(body, label)
        odds_columns = [
            name for name in results_df.columns if OddsColumn.parse(name)
        ]
        line_columns = [
            name
            for names in HANDICAP_LINE_COLUMNS.values()
            for name in names
            if name in results_df
        ]
        to_numbers(results_df, odds_columns + line_columns, label)
    _section(f"Unconverted values and dropped rows: "
             f"{len(capture.messages)} across {len(downloads)} files")
    for message in capture.messages:
        print(f"  {message}")


class _WarningCapture(logging.Handler):
    """Collect warning messages instead of printing them."""

    def __init__(self) -> None:
        super().__init__(logging.WARNING)
        self.messages: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.messages.append(record.getMessage())


def _alias_hints(team: str, candidates: list[str]) -> str:
    """Return similar names in the same country, as ' (alias? a, b)'."""
    others = [name for name in candidates if name != team]
    close = difflib.get_close_matches(
        team, others, n=3, cutoff=NAME_SIMILARITY
    )
    return f"  (alias? {', '.join(close)})" if close else ""


def _section(title: str) -> None:
    """Print a section heading."""
    print(f"\n== {title} ==")


if __name__ == "__main__":
    main()
