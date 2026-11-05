"""Check whether playoff and extra-round matches behave like the rest.

Finished matches are put in one of four groups per league-season:

- cross-tier: a team in it played 4 or fewer games that season, i.e. a
  promotion or relegation tie against a lower-division side
- post-season: played more than 7 days after the season's typical end
  (the median team's last match), e.g. MLS or Liga MX playoffs
- extra rounds: both teams are past a double round robin (game number
  above 2 × (teams − 1)), e.g. Scotland's third round and post-split
  games, or championship and relegation groups
- regular: everything else

For each group, overall and per league, it reports match counts,
home/draw/away rates, goals per game and the log-loss of Pinnacle's
closing odds. The database is opened read-only.

    python scripts/adhoc/playoff_analysis.py
"""
import sqlite3

import numpy as np
import pandas as pd

import _bootstrap  # noqa: F401

from scorecaster.config import Settings

PLAYOFF_ONLY_GAMES = 4
POST_SEASON_DAYS = 7

MATCHES = """
    SELECT m.id, c.code, m.season_id, m.match_date,
           m.home_team_id, m.away_team_id, m.ft_home, m.ft_away,
           o.home_price, o.draw_price, o.away_price
    FROM matches m
    JOIN competitions c ON c.id = m.competition_id
    LEFT JOIN (
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
    ) o ON o.match_id = m.id
    WHERE m.status = 'finished'
"""


def main() -> None:
    """Classify every finished match and print the comparisons."""
    matches_df = read_matches()
    matches_df["group"] = classify(matches_df)
    print(f"{len(matches_df)} finished matches\n")

    print("== All leagues ==")
    print(summarise(matches_df, ["group"]).round(3).to_string())

    print("\n== Non-regular matches by league ==")
    by_league_df = summarise(matches_df, ["code", "group"])
    share = by_league_df["matches"] / by_league_df.groupby("code")[
        "matches"
    ].transform("sum")
    by_league_df.insert(1, "share", share)
    non_regular = by_league_df.reset_index("group")
    non_regular = non_regular[non_regular["group"] != "regular"]
    print(non_regular.round(3).to_string())


def read_matches() -> pd.DataFrame:
    """Return finished matches with results and Pinnacle closing prices."""
    db_uri = f"file:{Settings.from_env().db_path}?mode=ro"
    with sqlite3.connect(db_uri, uri=True) as connection:
        matches_df = pd.read_sql_query(
            MATCHES, connection, parse_dates=["match_date"]
        )
    return matches_df.sort_values(["match_date", "id"]).reset_index(
        drop=True
    )


def classify(matches_df: pd.DataFrame) -> pd.Series:
    """Return each match's group: cross-tier, post-season, extra or regular."""
    sides_df = _team_sides(matches_df)
    games = sides_df.groupby(["season_id", "team_id"])["id"].transform("size")
    teams = sides_df.groupby("season_id")["team_id"].transform("nunique")
    sides_df["short_season"] = games <= PLAYOFF_ONLY_GAMES
    sides_df["beyond_double"] = sides_df["game_number"] > 2 * (teams - 1)

    per_match = sides_df.groupby("id").agg(
        cross_tier=("short_season", "any"),
        extra_round=("beyond_double", "all"),
    )
    last_match = sides_df.groupby(["season_id", "team_id"])[
        "match_date"
    ].max()
    typical_end = last_match.groupby("season_id").median()
    end = matches_df["season_id"].map(typical_end)
    post_season = matches_df["match_date"] > end + pd.Timedelta(
        days=POST_SEASON_DAYS
    )

    flags = matches_df[["id"]].join(per_match, on="id")
    groups = np.select(
        [flags["cross_tier"], post_season, flags["extra_round"]],
        ["cross-tier", "post-season", "extra rounds"],
        default="regular",
    )
    return pd.Series(groups, index=matches_df.index)


def summarise(matches_df: pd.DataFrame, group: list[str]) -> pd.DataFrame:
    """Return counts, result rates, goals and market log-loss per group."""
    stats_df = matches_df.assign(
        home_win=matches_df["ft_home"] > matches_df["ft_away"],
        draw=matches_df["ft_home"] == matches_df["ft_away"],
        away_win=matches_df["ft_home"] < matches_df["ft_away"],
        goals=matches_df["ft_home"] + matches_df["ft_away"],
        log_loss=_market_log_loss(matches_df),
    )
    return stats_df.groupby(group).agg(
        matches=("id", "size"),
        home_win=("home_win", "mean"),
        draw=("draw", "mean"),
        away_win=("away_win", "mean"),
        goals=("goals", "mean"),
        with_odds=("log_loss", "count"),
        log_loss=("log_loss", "mean"),
    )


def _team_sides(matches_df: pd.DataFrame) -> pd.DataFrame:
    """Return one row per team per match, with its game number that season."""
    columns = ["id", "season_id", "match_date"]
    home_df = matches_df[columns + ["home_team_id"]].rename(
        columns={"home_team_id": "team_id"}
    )
    away_df = matches_df[columns + ["away_team_id"]].rename(
        columns={"away_team_id": "team_id"}
    )
    sides_df = pd.concat([home_df, away_df]).sort_values(["match_date", "id"])
    sides_df["game_number"] = (
        sides_df.groupby(["season_id", "team_id"]).cumcount() + 1
    )
    return sides_df


def _market_log_loss(matches_df: pd.DataFrame) -> pd.Series:
    """Return −ln(margin-free probability of the actual result) per match.

    Empty where the match has no Pinnacle closing prices.
    """
    prices = matches_df[["home_price", "draw_price", "away_price"]]
    implied = 1 / prices
    probabilities = implied.div(implied.sum(axis=1), axis=0).to_numpy()
    outcome = np.select(
        [
            matches_df["ft_home"] > matches_df["ft_away"],
            matches_df["ft_home"] == matches_df["ft_away"],
        ],
        [0, 1],
        default=2,
    )
    chosen = probabilities[np.arange(len(matches_df)), outcome]
    return pd.Series(-np.log(chosen), index=matches_df.index)


if __name__ == "__main__":
    main()
