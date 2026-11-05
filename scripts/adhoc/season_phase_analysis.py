"""Compare results and market accuracy across the five phases of a season.

For every finished match with Pinnacle closing 1X2 odds, take the home
team's season phase (1 = first fifth of its season, 5 = last). Per
phase, overall and by league, report home/draw/away rates, average
goals, and the log-loss of the closing odds turned into probabilities.
A higher log-loss means the market predicted that phase less well. The
database is opened read-only.

    python scripts/adhoc/season_phase_analysis.py
"""
import sqlite3

import numpy as np
import pandas as pd

import _bootstrap  # noqa: F401

from scorecaster.config import Settings

MATCHES_WITH_CLOSING_ODDS = """
    SELECT c.code, f.home_season_phase AS phase, f.result,
           f.total_goals, o.home_price, o.draw_price, o.away_price
    FROM v_match_features f
    JOIN competitions c ON c.id = f.competition_id
    JOIN (
        SELECT match_id,
               MAX(CASE WHEN selection = 'home' THEN price END)
                   AS home_price,
               MAX(CASE WHEN selection = 'draw' THEN price END)
                   AS draw_price,
               MAX(CASE WHEN selection = 'away' THEN price END)
                   AS away_price
        FROM odds
        WHERE bookmaker = 'pinnacle' AND market = '1X2'
          AND timing = 'closing'
        GROUP BY match_id
    ) o ON o.match_id = f.match_id
    WHERE f.is_finished AND f.home_season_phase IS NOT NULL
"""


def main() -> None:
    """Load the matches, add probabilities, and print both tables."""
    phase_df = read_matches()
    phase_df = add_probabilities(phase_df)
    print(f"{len(phase_df)} matches with Pinnacle closing 1X2 odds\n")

    print("== By season phase, all leagues ==")
    print(summarise(phase_df, ["phase"]).round(3).to_string())

    print("\n== Log-loss by league and phase ==")
    by_league_df = summarise(phase_df, ["code", "phase"])
    log_loss_df = by_league_df["log_loss"].unstack("phase")
    log_loss_df["matches"] = by_league_df["matches"].groupby("code").sum()
    print(log_loss_df.round(3).to_string())


def read_matches() -> pd.DataFrame:
    """Return finished matches with their phase, result and closing odds."""
    db_uri = f"file:{Settings.from_env().db_path}?mode=ro"
    with sqlite3.connect(db_uri, uri=True) as connection:
        matches_df = pd.read_sql_query(
            MATCHES_WITH_CLOSING_ODDS, connection
        )
    prices = ["home_price", "draw_price", "away_price"]
    return matches_df.dropna(subset=prices)


def add_probabilities(phase_df: pd.DataFrame) -> pd.DataFrame:
    """Turn the three prices into probabilities without the margin.

    Each price's 1/odds is divided by the sum of all three, e.g.
    2.00 / 3.50 / 4.00 -> 0.50, 0.29, 0.25 -> 0.48, 0.27, 0.24.
    The probability given to the actual result is kept as `p_result`.
    """
    implied_df = 1 / phase_df[["home_price", "draw_price", "away_price"]]
    implied_df = implied_df.div(implied_df.sum(axis=1), axis=0)
    implied_df.columns = ["H", "D", "A"]
    phase_df = phase_df.copy()
    phase_df["p_result"] = implied_df.to_numpy()[
        np.arange(len(phase_df)),
        implied_df.columns.get_indexer(phase_df["result"]),
    ]
    return phase_df


def summarise(phase_df: pd.DataFrame, group: list[str]) -> pd.DataFrame:
    """Return result rates, goals and market log-loss for each group."""
    return phase_df.groupby(group).agg(
        matches=("result", "size"),
        home_win=("result", _share("H")),
        draw=("result", _share("D")),
        away_win=("result", _share("A")),
        goals=("total_goals", "mean"),
        log_loss=("p_result", _log_loss),
    )


def _share(outcome: str):
    """Return a function giving the share of results equal to `outcome`."""
    def share(results: pd.Series) -> float:
        return (results == outcome).mean()
    share.__name__ = f"share_{outcome}"
    return share


def _log_loss(p_result: pd.Series) -> float:
    """Return mean −ln(probability given to the actual result)."""
    return float(-np.log(p_result).mean())


if __name__ == "__main__":
    main()
