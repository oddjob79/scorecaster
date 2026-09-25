"""Loads the modelling views into pandas DataFrames."""
from __future__ import annotations

import pandas as pd

from percy.db import Database
from percy.features.schema import MATCH_VIEW, TEAM_VIEW


class DatasetLoader:
    """Reads feature views, optionally restricted to finished (trainable) or upcoming matches."""

    def __init__(self, db: Database) -> None:
        self.db = db

    def _read(self, view: str, finished: bool | None) -> pd.DataFrame:
        where = "" if finished is None else f" WHERE is_finished = {int(finished)}"
        return pd.read_sql_query(f"SELECT * FROM {view}{where} ORDER BY match_date, match_id",
                                 self.db.engine, parse_dates=["match_date"])

    def matches(self, finished: bool | None = True) -> pd.DataFrame:
        """One row per match with home_/away_ features and result, total_goals, over_2_5, btts targets."""
        return self._read(MATCH_VIEW, finished)

    def team_matches(self, finished: bool | None = True) -> pd.DataFrame:
        """One row per team per match with opp_ features and goals_for/goals_against/result_pts targets."""
        return self._read(TEAM_VIEW, finished)
