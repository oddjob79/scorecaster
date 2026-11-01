"""Derived `team_match_features` table and modelling views, generated from the calculator columns."""
from __future__ import annotations

from sqlalchemy import Boolean, Column, Date, Engine, Float, Integer, MetaData, Table, inspect, text

TABLE_NAME = "team_match_features"
TEAM_VIEW = "v_team_match_features"
MATCH_VIEW = "v_match_features"

KEY_COLUMNS = ["match_id", "team_id"]
CONTEXT_COLUMNS = ["opponent_id", "competition_id", "season_id", "match_date", "matchday", "is_home", "is_finished"]
TARGET_COLUMNS = ["goals_for", "goals_against", "result_pts"]


class FeatureTableSchema:
    """Builds, validates and (re)creates the wide feature table and its views."""

    def __init__(self, feature_columns: list[str]) -> None:
        if len(set(feature_columns)) != len(feature_columns):
            raise ValueError("duplicate feature column names")
        self.feature_columns = feature_columns
        self.metadata = MetaData()
        self.table = Table(
            TABLE_NAME, self.metadata,
            Column("match_id", Integer, primary_key=True),
            Column("team_id", Integer, primary_key=True),
            Column("opponent_id", Integer, nullable=False, index=True),
            Column("competition_id", Integer, nullable=False),
            Column("season_id", Integer, nullable=False, index=True),
            Column("match_date", Date, nullable=False, index=True),
            Column("matchday", Integer),
            Column("is_home", Boolean, nullable=False),
            Column("is_finished", Boolean, nullable=False),
            Column("goals_for", Integer),
            Column("goals_against", Integer),
            Column("result_pts", Integer),
            *[Column(name, Float) for name in feature_columns],
        )

    @property
    def all_columns(self) -> list[str]:
        return [c.name for c in self.table.columns]

    def matches_database(self, engine: Engine) -> bool:
        """True if the stored table has exactly the expected columns."""
        insp = inspect(engine)
        if not insp.has_table(TABLE_NAME):
            return False
        return [c["name"] for c in insp.get_columns(TABLE_NAME)] == self.all_columns

    def create(self, engine: Engine) -> None:
        self.metadata.create_all(engine, checkfirst=True)
        self.create_views(engine)

    def drop(self, engine: Engine) -> None:
        with engine.begin() as conn:
            conn.execute(text(f"DROP VIEW IF EXISTS {MATCH_VIEW}"))
            conn.execute(text(f"DROP VIEW IF EXISTS {TEAM_VIEW}"))
        self.metadata.drop_all(engine, checkfirst=True)

    def create_views(self, engine: Engine) -> None:
        """(Re)create the team-with-opponent view and the one-row-per-match view."""
        opp = ", ".join(f"o.{c} AS opp_{c}" for c in self.feature_columns)
        home = ", ".join(f"h.{c} AS home_{c}" for c in self.feature_columns)
        away = ", ".join(f"a.{c} AS away_{c}" for c in self.feature_columns)
        team_view = (
            f"CREATE VIEW {TEAM_VIEW} AS SELECT t.*, {opp} FROM {TABLE_NAME} t "
            f"JOIN {TABLE_NAME} o ON o.match_id = t.match_id AND o.team_id = t.opponent_id"
        )
        match_view = (
            f"CREATE VIEW {MATCH_VIEW} AS SELECT h.match_id, h.competition_id, h.season_id, h.match_date, "
            "h.matchday, h.is_finished, h.team_id AS home_team_id, a.team_id AS away_team_id, "
            "h.goals_for AS home_goals, a.goals_for AS away_goals, "
            "CASE WHEN NOT h.is_finished THEN NULL WHEN h.goals_for > a.goals_for THEN 'H' "
            "WHEN h.goals_for = a.goals_for THEN 'D' ELSE 'A' END AS result, "
            "h.goals_for + a.goals_for AS total_goals, "
            "CASE WHEN h.is_finished THEN h.goals_for + a.goals_for > 2 END AS over_2_5, "
            "CASE WHEN h.is_finished THEN h.goals_for > 0 AND a.goals_for > 0 END AS btts, "
            f"{home}, {away} FROM {TABLE_NAME} h "
            f"JOIN {TABLE_NAME} a ON a.match_id = h.match_id AND a.team_id = h.opponent_id WHERE h.is_home"
        )
        with engine.begin() as conn:
            conn.execute(text(f"DROP VIEW IF EXISTS {MATCH_VIEW}"))
            conn.execute(text(f"DROP VIEW IF EXISTS {TEAM_VIEW}"))
            conn.execute(text(team_view))
            conn.execute(text(match_view))
