"""Define the derived feature table and its two modelling views.

`team_match_features` has one row per team per match: context columns,
the result targets, then one float column per calculator feature. The
views pair each row with its opponent's features, or turn each match
into one row with home_ and away_ columns.
"""
from __future__ import annotations

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    Engine,
    Float,
    Integer,
    MetaData,
    Table,
    inspect,
    text,
)

TABLE_NAME = "team_match_features"
TEAM_VIEW = "v_team_match_features"
MATCH_VIEW = "v_match_features"


class FeatureTableSchema:
    """Create, check and drop the wide feature table and its views."""

    def __init__(self, feature_columns: list[str]) -> None:
        if len(set(feature_columns)) != len(feature_columns):
            raise ValueError("duplicate feature column names")
        self.feature_columns = feature_columns
        self.metadata = MetaData()
        self.table = Table(
            TABLE_NAME,
            self.metadata,
            Column("match_id", Integer, primary_key=True),
            Column("team_id", Integer, primary_key=True),
            Column("opponent_id", Integer, nullable=False, index=True),
            Column("competition_id", Integer, nullable=False),
            Column("season_id", Integer, nullable=False, index=True),
            Column("match_date", Date, nullable=False, index=True),
            Column("is_home", Boolean, nullable=False),
            Column("is_finished", Boolean, nullable=False),
            Column("goals_for", Integer),
            Column("goals_against", Integer),
            Column("result_pts", Integer),
            *[Column(name, Float) for name in feature_columns],
        )

    @property
    def all_columns(self) -> list[str]:
        """Return every column name in table order."""
        return [column.name for column in self.table.columns]

    def matches_database(self, engine: Engine) -> bool:
        """Return True if the stored table has exactly these columns."""
        inspector = inspect(engine)
        if not inspector.has_table(TABLE_NAME):
            return False
        stored = [c["name"] for c in inspector.get_columns(TABLE_NAME)]
        return stored == self.all_columns

    def create(self, engine: Engine) -> None:
        """Create the table if missing, and (re)create the views."""
        self.metadata.create_all(engine, checkfirst=True)
        self.create_views(engine)

    def drop(self, engine: Engine) -> None:
        """Drop the views and the table."""
        with engine.begin() as connection:
            connection.execute(text(f"DROP VIEW IF EXISTS {MATCH_VIEW}"))
            connection.execute(text(f"DROP VIEW IF EXISTS {TEAM_VIEW}"))
        self.metadata.drop_all(engine, checkfirst=True)

    def create_views(self, engine: Engine) -> None:
        """Recreate the team-with-opponent and one-row-per-match views."""
        with engine.begin() as connection:
            connection.execute(text(f"DROP VIEW IF EXISTS {MATCH_VIEW}"))
            connection.execute(text(f"DROP VIEW IF EXISTS {TEAM_VIEW}"))
            connection.execute(text(self._team_view_sql()))
            connection.execute(text(self._match_view_sql()))

    def _team_view_sql(self) -> str:
        """Return SQL for one row per team, with the opponent's features."""
        opponent = _prefixed("o", "opp", self.feature_columns)
        return (
            f"CREATE VIEW {TEAM_VIEW} AS "
            f"SELECT t.*, {opponent} "
            f"FROM {TABLE_NAME} t "
            f"JOIN {TABLE_NAME} o "
            "ON o.match_id = t.match_id AND o.team_id = t.opponent_id"
        )

    def _match_view_sql(self) -> str:
        """Return SQL for one row per match with home_ and away_ features.

        Targets: result (H/D/A), total goals, over 2.5 and both teams to
        score, all empty until the match is finished.
        """
        home = _prefixed("h", "home", self.feature_columns)
        away = _prefixed("a", "away", self.feature_columns)
        return (
            f"CREATE VIEW {MATCH_VIEW} AS SELECT "
            "h.match_id, h.competition_id, h.season_id, h.match_date, "
            "h.is_finished, "
            "h.team_id AS home_team_id, a.team_id AS away_team_id, "
            "h.goals_for AS home_goals, a.goals_for AS away_goals, "
            "CASE WHEN NOT h.is_finished THEN NULL "
            "WHEN h.goals_for > a.goals_for THEN 'H' "
            "WHEN h.goals_for = a.goals_for THEN 'D' "
            "ELSE 'A' END AS result, "
            "h.goals_for + a.goals_for AS total_goals, "
            "CASE WHEN h.is_finished "
            "THEN h.goals_for + a.goals_for > 2 END AS over_2_5, "
            "CASE WHEN h.is_finished "
            "THEN h.goals_for > 0 AND a.goals_for > 0 END AS btts, "
            f"{home}, {away} "
            f"FROM {TABLE_NAME} h "
            f"JOIN {TABLE_NAME} a "
            "ON a.match_id = h.match_id AND a.team_id = h.opponent_id "
            "WHERE h.is_home"
        )


def _prefixed(alias: str, prefix: str, columns: list[str]) -> str:
    """Return 'alias.col AS prefix_col, ...' for every column."""
    return ", ".join(f"{alias}.{c} AS {prefix}_{c}" for c in columns)
