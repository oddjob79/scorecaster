"""Compute pre-match feature columns for one team in one match.

Each calculator owns a fixed set of columns and fills them from a
`MatchContext`, which only holds what was known before kick-off.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from math import ceil
from typing import Callable

from scorecaster.config import FeatureConfig
from scorecaster.features.history import TeamMatchRecord
from scorecaster.features.state import MatchContext, safe_div

Features = dict[str, float | int | None]
RecordTest = Callable[[TeamMatchRecord], bool]


class FeatureCalculator(ABC):
    """Produce a fixed set of pre-match feature columns."""

    @abstractmethod
    def columns(self) -> list[str]:
        """Return the column names this calculator fills."""

    @abstractmethod
    def compute(self, ctx: MatchContext) -> Features:
        """Return the feature values for the team in `ctx`."""


class ExperienceCalculator(FeatureCalculator):
    """Games played, rest days, and which fifth of the season this is."""

    def columns(self) -> list[str]:
        return [
            "matches_played_total",
            "matches_played_season",
            "rest_days",
            "season_phase",
        ]

    def compute(self, ctx: MatchContext) -> Features:
        records = ctx.history.records
        played_this_season = len(ctx.history.season(ctx.season_id))
        rest_days = (ctx.day - records[-1].day).days if records else None
        return {
            "matches_played_total": len(records),
            "matches_played_season": played_this_season,
            "rest_days": rest_days,
            "season_phase": season_phase(
                played_this_season + 1, ctx.state.season_games(ctx.season_id)
            ),
        }


class PreviousResultCalculator(FeatureCalculator):
    """Most recent result overall, at home and away (points 3/1/0)."""

    def columns(self) -> list[str]:
        return [
            "prev_pts",
            "prev_gf",
            "prev_ga",
            "prev_home_pts",
            "prev_away_pts",
        ]

    def compute(self, ctx: MatchContext) -> Features:
        last = _latest(ctx.history.last(1))
        last_home = _latest(ctx.history.last(1, venue=True))
        last_away = _latest(ctx.history.last(1, venue=False))
        return {
            "prev_pts": last.points if last else None,
            "prev_gf": last.gf if last else None,
            "prev_ga": last.ga if last else None,
            "prev_home_pts": last_home.points if last_home else None,
            "prev_away_pts": last_away.points if last_away else None,
        }


class FormCalculator(FeatureCalculator):
    """Points, wins, draws and losses over the last N games.

    With `venue` set, only home (True) or away (False) games count. A
    window is left empty until the team has played N such games.
    """

    STATS = ("pts", "wins", "draws", "losses")

    def __init__(
        self, windows: tuple[int, ...], venue: bool | None = None
    ) -> None:
        self.windows = windows
        self.venue = venue
        self.prefix = _venue_prefix(venue, "form")

    def columns(self) -> list[str]:
        return [
            f"{self.prefix}_{n}_{stat}"
            for n in self.windows
            for stat in self.STATS
        ]

    def compute(self, ctx: MatchContext) -> Features:
        features: Features = {}
        for n in self.windows:
            records = ctx.history.last(n, venue=self.venue)
            values = {
                "pts": sum(r.points for r in records),
                "wins": sum(r.won for r in records),
                "draws": sum(r.drawn for r in records),
                "losses": sum(r.lost for r in records),
            }
            full = len(records) == n
            for stat in self.STATS:
                features[f"{self.prefix}_{n}_{stat}"] = (
                    values[stat] if full else None
                )
        return features


class GoalsCalculator(FeatureCalculator):
    """Goals for and against, and goal-event counts, over the last N games."""

    STATS = ("gf", "ga", "clean_sheets", "failed_to_score", "btts", "over25")

    def __init__(
        self, windows: tuple[int, ...], venue: bool | None = None
    ) -> None:
        self.windows = windows
        self.venue = venue
        self.prefix = _venue_prefix(venue, "goals")

    def columns(self) -> list[str]:
        return [
            f"{self.prefix}_{n}_{stat}"
            for n in self.windows
            for stat in self.STATS
        ]

    def compute(self, ctx: MatchContext) -> Features:
        features: Features = {}
        for n in self.windows:
            records = ctx.history.last(n, venue=self.venue)
            values = {
                "gf": sum(r.gf for r in records),
                "ga": sum(r.ga for r in records),
                "clean_sheets": sum(r.ga == 0 for r in records),
                "failed_to_score": sum(r.gf == 0 for r in records),
                "btts": sum(r.gf > 0 and r.ga > 0 for r in records),
                "over25": sum(r.gf + r.ga > 2 for r in records),
            }
            full = len(records) == n
            for stat in self.STATS:
                features[f"{self.prefix}_{n}_{stat}"] = (
                    values[stat] if full else None
                )
        return features


def _won(record: TeamMatchRecord) -> bool:
    return record.won


def _unbeaten(record: TeamMatchRecord) -> bool:
    return not record.lost


def _winless(record: TeamMatchRecord) -> bool:
    return not record.won


def _lost(record: TeamMatchRecord) -> bool:
    return record.lost


def _scored(record: TeamMatchRecord) -> bool:
    return record.gf > 0


def _kept_clean_sheet(record: TeamMatchRecord) -> bool:
    return record.ga == 0


class StreakCalculator(FeatureCalculator):
    """Length of the current run of wins, unbeaten games, and so on."""

    STREAKS: dict[str, RecordTest] = {
        "streak_wins": _won,
        "streak_unbeaten": _unbeaten,
        "streak_winless": _winless,
        "streak_losses": _lost,
        "streak_scoring": _scored,
        "streak_clean_sheets": _kept_clean_sheet,
    }

    def columns(self) -> list[str]:
        return list(self.STREAKS)

    def compute(self, ctx: MatchContext) -> Features:
        records = ctx.history.records
        if not records:
            return dict.fromkeys(self.STREAKS)
        return {
            name: _run_length(records, test)
            for name, test in self.STREAKS.items()
        }


class SeasonCalculator(FeatureCalculator):
    """Season-to-date points and per-game rates, overall and by venue."""

    def columns(self) -> list[str]:
        return [
            "season_pts",
            "season_ppg",
            "season_gf_pg",
            "season_ga_pg",
            "season_gd",
            "season_home_ppg",
            "season_away_ppg",
        ]

    def compute(self, ctx: MatchContext) -> Features:
        records = ctx.history.season(ctx.season_id)
        home = [r for r in records if r.is_home]
        away = [r for r in records if not r.is_home]
        points = sum(r.points for r in records)
        home_points = sum(r.points for r in home)
        away_points = sum(r.points for r in away)
        return {
            "season_pts": points,
            "season_ppg": safe_div(points, len(records)),
            "season_gf_pg": safe_div(sum(r.gf for r in records), len(records)),
            "season_ga_pg": safe_div(sum(r.ga for r in records), len(records)),
            "season_gd": sum(r.gf - r.ga for r in records),
            "season_home_ppg": safe_div(home_points, len(home)),
            "season_away_ppg": safe_div(away_points, len(away)),
        }


class TableCalculator(FeatureCalculator):
    """League position, band, gap to the top, and last season's finish."""

    def columns(self) -> list[str]:
        return [
            "league_position",
            "position_band",
            "points_to_top",
            "prev_season_position",
        ]

    def compute(self, ctx: MatchContext) -> Features:
        table = ctx.table
        points = table.row(ctx.team_id).points
        top = table.points_at(1)
        return {
            "league_position": table.position(ctx.team_id),
            "position_band": ctx.state.band(ctx.team_id, ctx.season_id),
            "points_to_top": top - points if top is not None else None,
            "prev_season_position": ctx.state.previous_position(
                ctx.team_id, ctx.season_id
            ),
        }


class StrengthCalculator(FeatureCalculator):
    """Elo rating and expectation, and attack and defence strength.

    Attack and defence strength are goals scored and conceded per game
    against the league's average, once the team has played enough.
    """

    def __init__(self, cfg: FeatureConfig) -> None:
        self.cfg = cfg

    def columns(self) -> list[str]:
        return ["elo", "elo_expected", "attack_strength", "defence_strength"]

    def compute(self, ctx: MatchContext) -> Features:
        elo = ctx.state.elo
        row = ctx.table.row(ctx.team_id)
        league_average = ctx.table.goals_per_team_game()
        enough = row.played >= self.cfg.min_games_for_strength
        if not (enough and league_average):
            attack = defence = None
        else:
            attack = (row.gf / row.played) / league_average
            defence = (row.ga / row.played) / league_average
        return {
            "elo": elo.rating(ctx.team_id, ctx.competition_id),
            "elo_expected": elo.expected(
                ctx.team_id, ctx.opponent_id, ctx.is_home, ctx.competition_id
            ),
            "attack_strength": attack,
            "defence_strength": defence,
        }


class HeadToHeadCalculator(FeatureCalculator):
    """Recent record against this opponent, overall and at this venue."""

    def __init__(self, last_n: int, venue_last_n: int) -> None:
        self.last_n = last_n
        self.venue_last_n = venue_last_n

    def columns(self) -> list[str]:
        return [
            "h2h_played", "h2h_pts", "h2h_wins", "h2h_draws", "h2h_losses",
            "h2h_gf", "h2h_ga", "h2h_prev_pts",
            "h2h_venue_played", "h2h_venue_pts", "h2h_venue_gf",
            "h2h_venue_ga",
        ]

    def compute(self, ctx: MatchContext) -> Features:
        def against_opponent(record: TeamMatchRecord) -> bool:
            return record.opponent_id == ctx.opponent_id

        meetings = ctx.history.last(self.last_n, where=against_opponent)
        at_venue = ctx.history.last(
            self.venue_last_n, venue=ctx.is_home, where=against_opponent
        )
        features = {"h2h_played": len(meetings)}
        features |= _totals("h2h", meetings, with_results=True)
        features["h2h_prev_pts"] = meetings[-1].points if meetings else None
        features["h2h_venue_played"] = len(at_venue)
        features |= _totals("h2h_venue", at_venue, with_results=False)
        return features


class SimilarOpponentCalculator(FeatureCalculator):
    """Record against teams that were in the opponent's current band.

    Each past match is judged by the band its opponent was in at the
    time, so this is "form against teams like this one".
    """

    def __init__(self, last_n: int) -> None:
        self.last_n = last_n

    def columns(self) -> list[str]:
        return [
            "opponent_band",
            "vs_band_played",
            "vs_band_ppg",
            "vs_band_gf_pg",
            "vs_band_ga_pg",
        ]

    def compute(self, ctx: MatchContext) -> Features:
        band = ctx.state.band(ctx.opponent_id, ctx.season_id)

        def in_same_band(record: TeamMatchRecord) -> bool:
            return record.opponent_band == band

        records = (
            ctx.history.last(self.last_n, where=in_same_band) if band else []
        )
        played = len(records)
        return {
            "opponent_band": band,
            "vs_band_played": played,
            "vs_band_ppg": safe_div(sum(r.points for r in records), played),
            "vs_band_gf_pg": safe_div(sum(r.gf for r in records), played),
            "vs_band_ga_pg": safe_div(sum(r.ga for r in records), played),
        }


def default_calculators(cfg: FeatureConfig) -> list[FeatureCalculator]:
    """Return the standard calculator set used by the feature builder."""
    return [
        ExperienceCalculator(),
        PreviousResultCalculator(),
        FormCalculator(cfg.form_windows),
        FormCalculator(cfg.venue_windows, venue=True),
        FormCalculator(cfg.venue_windows, venue=False),
        GoalsCalculator(cfg.goal_windows),
        GoalsCalculator(cfg.venue_windows, venue=True),
        GoalsCalculator(cfg.venue_windows, venue=False),
        StreakCalculator(),
        SeasonCalculator(),
        TableCalculator(),
        StrengthCalculator(cfg),
        HeadToHeadCalculator(cfg.h2h_last_n, cfg.h2h_venue_last_n),
        SimilarOpponentCalculator(cfg.similar_opponent_last_n),
    ]


def season_phase(game_number: int, season_games: int | None) -> int | None:
    """Return which fifth of its season a team's game falls in (1–5).

    Premier League, 38 games: games 1–7 -> 1, 8–15 -> 2, 31–38 -> 5.
    Games beyond the season length (e.g. playoff rounds) stay in 5.
    """
    if not season_games:
        return None
    return min(5, ceil(5 * game_number / season_games))


def _totals(
    prefix: str, records: list[TeamMatchRecord], with_results: bool
) -> Features:
    """Return points and goals for a set of meetings, empty if none."""
    names = ["pts", "gf", "ga"]
    if with_results:
        names = ["pts", "wins", "draws", "losses", "gf", "ga"]
    values = {
        "pts": sum(r.points for r in records),
        "wins": sum(r.won for r in records),
        "draws": sum(r.drawn for r in records),
        "losses": sum(r.lost for r in records),
        "gf": sum(r.gf for r in records),
        "ga": sum(r.ga for r in records),
    }
    return {
        f"{prefix}_{name}": values[name] if records else None
        for name in names
    }


def _latest(records: list[TeamMatchRecord]) -> TeamMatchRecord | None:
    """Return the last record, or None if there are none."""
    return records[-1] if records else None


def _run_length(records: list[TeamMatchRecord], test: RecordTest) -> int:
    """Count how many of the latest records in a row pass the test."""
    count = 0
    for record in reversed(records):
        if not test(record):
            break
        count += 1
    return count


def _venue_prefix(venue: bool | None, base: str) -> str:
    """Return the column prefix: 'form', 'home_form' or 'away_form'."""
    if venue is None:
        return base
    return f"{'home' if venue else 'away'}_{base}"
