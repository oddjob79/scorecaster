"""Measure how promoted and relegated teams do in their new league.

For every main-league season, find the newcomers: teams that played in
a different tier of the same country the season before. For each, take
its finishing position as a percentile of the table (0 top, 1 bottom)
and its points per game over its first 10 matches minus the league
average. Summaries are printed per tier boundary and direction, then
split by previous finish and by era. The database is opened read-only.

    python scripts/adhoc/promotion_analysis.py
"""
import sqlite3

import numpy as np
import pandas as pd

import _bootstrap  # noqa: F401

from scorecaster.config import Settings
from scorecaster.leagues import LEAGUES, current_season_start

FIRST_GAMES = 10
ERA_SPLIT = 2013  # 2005/06–2012/13 against 2013/14 onward
MAIN_LEAGUE_CODES = [
    league.code for league in LEAGUES if league.file_style == "season"
]

# One row per team per finished main-league match.
TEAM_GAMES = """
    SELECT c.code, c.country, c.tier, s.start_year, m.match_date,
           side.team_id, side.goals_for, side.goals_against
    FROM matches m
    JOIN competitions c ON c.id = m.competition_id
    JOIN seasons s ON s.id = m.season_id
    JOIN (
        SELECT id, home_team_id AS team_id,
               ft_home AS goals_for, ft_away AS goals_against
        FROM matches
        UNION ALL
        SELECT id, away_team_id, ft_away, ft_home
        FROM matches
    ) AS side ON side.id = m.id
    WHERE m.status = 'finished'
"""


def main() -> None:
    """Build the newcomer table and print every summary."""
    games_df = read_team_games()
    standings_df = build_standings(games_df)
    newcomers_df = find_newcomers(standings_df)
    seasons = standings_df.groupby(["code", "start_year"]).ngroups
    print(f"{len(newcomers_df)} newcomers in {seasons} league-seasons\n")

    group = ["boundary", "direction"]
    print_summary("By boundary and direction", newcomers_df, group)
    print_summary(
        "By previous finish", newcomers_df, [*group, "previous_finish"]
    )
    print_summary("By era", newcomers_df, [*group, "era"])


def read_team_games() -> pd.DataFrame:
    """Return one row per team per finished match, with points earned.

    Main leagues only, in completed seasons: the season in progress
    has no final table yet.
    """
    db_uri = f"file:{Settings.from_env().db_path}?mode=ro"
    with sqlite3.connect(db_uri, uri=True) as connection:
        games_df = pd.read_sql_query(TEAM_GAMES, connection)
    games_df = games_df[
        games_df["code"].isin(MAIN_LEAGUE_CODES)
        & (games_df["start_year"] < current_season_start())
    ].copy()
    goal_difference = games_df["goals_for"] - games_df["goals_against"]
    games_df["points"] = np.select(
        [goal_difference > 0, goal_difference == 0], [3, 1], default=0
    )
    return games_df


def build_standings(games_df: pd.DataFrame) -> pd.DataFrame:
    """Return each team's final table position and first-10-games form.

    Tables are rebuilt from results: points, then goal difference, then
    goals scored. Deductions and split-league playoffs aren't modelled.
    """
    season = ["code", "country", "tier", "start_year"]
    totals_df = games_df.groupby([*season, "team_id"], as_index=False).agg(
        points=("points", "sum"),
        goals_for=("goals_for", "sum"),
        goals_against=("goals_against", "sum"),
        games=("points", "size"),
    )
    totals_df["goal_difference"] = (
        totals_df["goals_for"] - totals_df["goals_against"]
    )
    totals_df = totals_df.sort_values(
        [*season, "points", "goal_difference", "goals_for"],
        ascending=[True, True, True, True, False, False, False],
    )
    totals_df["position"] = totals_df.groupby(season).cumcount() + 1
    totals_df["league_size"] = totals_df.groupby(season)["team_id"].transform(
        "size"
    )
    totals_df["finish_pct"] = (totals_df["position"] - 1) / (
        totals_df["league_size"] - 1
    )
    form_df = _first_games_form(games_df, season)
    return totals_df.merge(form_df, on=[*season, "team_id"])


def _first_games_form(
    games_df: pd.DataFrame, season: list[str]
) -> pd.DataFrame:
    """Return each team's first-10 points per game minus the league's."""
    ordered_df = games_df.sort_values("match_date")
    first_df = ordered_df.groupby([*season, "team_id"]).head(FIRST_GAMES)
    form_df = first_df.groupby([*season, "team_id"], as_index=False).agg(
        first_ppg=("points", "mean")
    )
    league_ppg = games_df.groupby(season)["points"].mean().rename("league_ppg")
    form_df = form_df.merge(league_ppg.reset_index(), on=season)
    form_df["first_ppg_vs_avg"] = form_df["first_ppg"] - form_df["league_ppg"]
    return form_df[[*season, "team_id", "first_ppg_vs_avg"]]


def find_newcomers(standings_df: pd.DataFrame) -> pd.DataFrame:
    """Return the teams that changed tier, with where they came from.

    A team counts as promoted into the bottom tier when it wasn't in any
    loaded league the season before. Each league's first loaded season
    is skipped, since there is no previous season to compare with.
    """
    previous_df = standings_df[
        ["country", "start_year", "team_id", "code", "tier", "position"]
    ].rename(columns={
        "code": "previous_code",
        "tier": "previous_tier",
        "position": "previous_position",
    })
    previous_df["start_year"] += 1
    merged_df = standings_df.merge(
        previous_df, on=["country", "start_year", "team_id"], how="left"
    )
    first_season = merged_df.groupby("code")["start_year"].transform("min")
    merged_df = merged_df[merged_df["start_year"] > first_season]

    bottom_tier = merged_df.groupby("country")["tier"].transform("max")
    from_outside = merged_df["previous_tier"].isna() & (
        merged_df["tier"] == bottom_tier
    )
    moved = merged_df["previous_tier"].notna() & (
        merged_df["previous_tier"] != merged_df["tier"]
    )
    newcomers_df = merged_df[moved | from_outside].copy()

    came_down = newcomers_df["previous_tier"] < newcomers_df["tier"]
    newcomers_df["direction"] = np.where(came_down, "relegated", "promoted")
    newcomers_df["boundary"] = (
        newcomers_df["code"]
        + " ← "
        + newcomers_df["previous_code"].fillna("outside")
    )
    newcomers_df["previous_finish"] = _previous_finish(newcomers_df)
    newcomers_df["era"] = np.where(
        newcomers_df["start_year"] < ERA_SPLIT, "2005–2012", "2013–"
    )
    return newcomers_df


def _previous_finish(newcomers_df: pd.DataFrame) -> pd.Series:
    """Label how each newcomer finished in its previous league.

    If n teams went up from a league-season, a promoted team that
    finished below nth came through the playoffs.
    """
    promoted = newcomers_df["direction"] == "promoted"
    going_up = (
        newcomers_df[promoted]
        .groupby(["previous_code", "start_year"])["team_id"]
        .transform("size")
        .reindex(newcomers_df.index)
    )
    labels = pd.Series("relegated: other", index=newcomers_df.index)
    labels[promoted] = "promoted: other top places"
    labels[promoted & (newcomers_df["previous_position"] > going_up)] = (
        "promoted: from below (playoff)"
    )
    labels[promoted & (newcomers_df["previous_position"] == 1)] = (
        "promoted: champion"
    )
    labels[promoted & newcomers_df["previous_code"].isna()] = (
        "promoted: from outside"
    )
    previous_size = newcomers_df["previous_position"].groupby(
        [newcomers_df["previous_code"], newcomers_df["start_year"]]
    ).transform("max")
    is_bottom = newcomers_df["previous_position"] == previous_size
    labels[~promoted & is_bottom] = "relegated: bottom place"
    return labels


def print_summary(
    title: str, newcomers_df: pd.DataFrame, group: list[str]
) -> None:
    """Print count, mean and spread of both measures for each group."""
    summary_df = newcomers_df.groupby(group).agg(
        n=("team_id", "size"),
        finish_mean=("finish_pct", "mean"),
        finish_sd=("finish_pct", "std"),
        finish_min=("finish_pct", "min"),
        finish_max=("finish_pct", "max"),
        first10_mean=("first_ppg_vs_avg", "mean"),
        first10_sd=("first_ppg_vs_avg", "std"),
    )
    print(f"== {title} ==")
    print(summary_df.round(2).to_string())
    print()


if __name__ == "__main__":
    main()
