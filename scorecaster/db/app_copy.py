"""Build the stats app's read-only copy of the database.

The copy holds the competitions, seasons, matches, teams, features and
market-average odds the stats app shows, with ids unchanged. It is built
beside the target file and swapped in only after it passes its checks.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

APP_COUNTRIES = (
    "England",
    "Scotland",
    "Germany",
    "Spain",
    "Italy",
    "France",
    "Netherlands",
    "Portugal",
    "Belgium",
)
FIRST_SEASON = 2016
APP_STATUSES = ("finished", "scheduled")
APP_BOOKMAKER = "market_avg"


class AppDatabaseError(Exception):
    """Raised when the built copy fails its integrity or key checks."""


@dataclass(frozen=True)
class TableCopy:
    """One table to copy: its name and the SELECT that picks its rows."""

    table: str
    select: str


# Parents before the tables that filter on them. Each SELECT reads the
# source (src) and the rows already copied into the new file (main).
TABLE_COPIES = (
    TableCopy(
        "competitions",
        "SELECT * FROM src.competitions WHERE country IN ({countries})",
    ),
    TableCopy(
        "seasons",
        "SELECT * FROM src.seasons"
        " WHERE competition_id IN (SELECT id FROM main.competitions)"
        " AND start_year >= :first_season",
    ),
    TableCopy(
        "matches",
        "SELECT * FROM src.matches"
        " WHERE season_id IN (SELECT id FROM main.seasons)"
        " AND status IN ({statuses})",
    ),
    TableCopy(
        "teams",
        "SELECT * FROM src.teams WHERE id IN ("
        " SELECT home_team_id FROM main.matches"
        " UNION SELECT away_team_id FROM main.matches)",
    ),
    TableCopy(
        "team_match_features",
        "SELECT * FROM src.team_match_features"
        " WHERE match_id IN (SELECT id FROM main.matches)",
    ),
    TableCopy(
        "odds",
        "SELECT * FROM src.odds WHERE bookmaker = :bookmaker"
        " AND match_id IN (SELECT id FROM main.matches)",
    ),
)
COPIED_TABLES = tuple(copy.table for copy in TABLE_COPIES)


class AppDatabaseBuilder:
    """Build the app database from the full one."""

    def __init__(self, source: Path, target: Path) -> None:
        self.source = source
        self.target = target
        self.staging = target.with_name(target.name + ".tmp")

    def build(self) -> dict[str, int]:
        """Build, check and swap in the copy; return rows per table.

        Raises AppDatabaseError listing the problems if a check fails,
        and leaves any existing target file untouched.
        """
        self.staging.unlink(missing_ok=True)
        connection = sqlite3.connect(self.staging.resolve().as_uri(), uri=True)
        try:
            connection.execute(
                "ATTACH DATABASE ? AS src",
                (self.source.resolve().as_uri() + "?mode=ro",),
            )
            self._create_tables(connection)
            counts = self._copy_rows(connection)
            connection.commit()
            # Detached first, so the checks look at the copy alone.
            connection.execute("DETACH DATABASE src")
            problems = self._problems(connection)
        finally:
            connection.close()
        if problems:
            raise AppDatabaseError("\n".join(problems))
        self.staging.replace(self.target)
        return counts

    def _create_tables(self, connection: sqlite3.Connection) -> None:
        """Create each copied table and its indexes from the source."""
        tables, table_params = _in_list("table", COPIED_TABLES)
        statements = connection.execute(
            "SELECT sql FROM src.sqlite_master"
            f" WHERE tbl_name IN ({tables}) AND sql IS NOT NULL"
            " ORDER BY type = 'index'",
            table_params,
        ).fetchall()
        for (statement,) in statements:
            connection.execute(statement)

    def _copy_rows(self, connection: sqlite3.Connection) -> dict[str, int]:
        """Insert each table's rows in TABLE_COPIES order; return counts."""
        countries, country_params = _in_list("country", APP_COUNTRIES)
        statuses, status_params = _in_list("status", APP_STATUSES)
        params = {
            **country_params,
            **status_params,
            "first_season": FIRST_SEASON,
            "bookmaker": APP_BOOKMAKER,
        }
        counts = {}
        for copy in TABLE_COPIES:
            select = copy.select.format(
                countries=countries, statuses=statuses
            )
            cursor = connection.execute(
                f"INSERT INTO main.{copy.table} {select}", params
            )
            counts[copy.table] = cursor.rowcount
        return counts

    def _problems(self, connection: sqlite3.Connection) -> list[str]:
        """Return integrity and foreign-key problems; empty when sound."""
        problems = []
        integrity = [
            row[0] for row in connection.execute("PRAGMA integrity_check")
        ]
        if integrity != ["ok"]:
            problems.extend(integrity)
        for table, rowid, parent, _ in connection.execute(
            "PRAGMA foreign_key_check"
        ):
            problems.append(f"{table} row {rowid}: no matching {parent} row")
        return problems


def _in_list(name: str, values: tuple[str, ...]) -> tuple[str, dict]:
    """Return named placeholders for an IN list and the values they bind.

    ("country", ("England", "Spain"))
    -> (":country0, :country1", {"country0": "England", "country1": "Spain"})
    """
    params = {f"{name}{index}": value for index, value in enumerate(values)}
    placeholders = ", ".join(f":{key}" for key in params)
    return placeholders, params
