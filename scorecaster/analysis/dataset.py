"""Load the modelling views into pandas DataFrames."""
from __future__ import annotations

import pandas as pd

from scorecaster.db import Database
from scorecaster.features.schema import MATCH_VIEW, TEAM_VIEW


class DatasetLoader:
    """Read the feature views, for finished matches, upcoming ones, or both.

    `finished` True gives trainable rows with results, False gives
    upcoming fixtures, None gives everything.
    """

    def __init__(self, db: Database) -> None:
        self.db = db

    def matches(self, finished: bool | None = True) -> pd.DataFrame:
        """Return one row per match, with home_ and away_ features.

        Targets: result, total_goals, over_2_5 and btts.
        """
        return self._read(MATCH_VIEW, finished)

    def team_matches(self, finished: bool | None = True) -> pd.DataFrame:
        """Return one row per team per match, with opp_ features.

        Targets: goals_for, goals_against and result_pts.
        """
        return self._read(TEAM_VIEW, finished)

    def _read(self, view: str, finished: bool | None) -> pd.DataFrame:
        """Read a view, filtered by finished state, in date order."""
        where = ""
        if finished is not None:
            where = f" WHERE is_finished = {int(finished)}"
        query = f"SELECT * FROM {view}{where} ORDER BY match_date, match_id"
        return pd.read_sql_query(
            query, self.db.engine, parse_dates=["match_date"]
        )
