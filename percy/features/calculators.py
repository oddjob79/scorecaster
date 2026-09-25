"""Feature calculators: each owns a set of columns and computes them from a MatchContext."""
from __future__ import annotations

from abc import ABC, abstractmethod

from percy.config import FeatureConfig
from percy.features.state import MatchContext, TeamMatchRecord, safe_div

Features = dict[str, float | int | None]


class FeatureCalculator(ABC):
    """Produces a fixed set of pre-match feature columns."""

    @abstractmethod
    def columns(self) -> list[str]:
        """Column names this calculator emits."""

    @abstractmethod
    def compute(self, ctx: MatchContext) -> Features:
        """Feature values for the team in `ctx`, using only pre-match state."""


def _venue_prefix(venue: bool | None, base: str) -> str:
    return base if venue is None else f"{'home' if venue else 'away'}_{base}"


def _streak(records: list[TeamMatchRecord], predicate) -> int:
    count = 0
    for rec in reversed(records):
        if not predicate(rec):
            break
        count += 1
    return count


class ExperienceCalculator(FeatureCalculator):
    """Sample sizes and rest days."""

    def columns(self) -> list[str]:
        return ["matches_played_total", "matches_played_season", "rest_days"]

    def compute(self, ctx: MatchContext) -> Features:
        recs = ctx.history.records
        return {
            "matches_played_total": len(recs),
            "matches_played_season": len(ctx.history.season(ctx.season_id)),
            "rest_days": (ctx.day - recs[-1].day).days if recs else None,
        }


class PreviousResultCalculator(FeatureCalculator):
    """Most recent result overall, at home and away (points 3/1/0)."""

    def columns(self) -> list[str]:
        return ["prev_pts", "prev_gf", "prev_ga", "prev_home_pts", "prev_away_pts"]

    def compute(self, ctx: MatchContext) -> Features:
        last, home, away = ctx.history.last(1), ctx.history.last(1, venue=True), ctx.history.last(1, venue=False)
        return {
            "prev_pts": last[0].points if last else None,
            "prev_gf": last[0].gf if last else None,
            "prev_ga": last[0].ga if last else None,
            "prev_home_pts": home[0].points if home else None,
            "prev_away_pts": away[0].points if away else None,
        }


class FormCalculator(FeatureCalculator):
    """Points, wins, draws and losses over the last N games (optionally home/away only)."""

    def __init__(self, windows: tuple[int, ...], venue: bool | None = None) -> None:
        self.windows = windows
        self.venue = venue
        self.prefix = _venue_prefix(venue, "form")

    def columns(self) -> list[str]:
        return [f"{self.prefix}_{n}_{s}" for n in self.windows for s in ("pts", "wins", "draws", "losses")]

    def compute(self, ctx: MatchContext) -> Features:
        out: Features = {}
        for n in self.windows:
            recs = ctx.history.last(n, venue=self.venue)
            full = len(recs) == n
            out[f"{self.prefix}_{n}_pts"] = sum(r.points for r in recs) if full else None
            out[f"{self.prefix}_{n}_wins"] = sum(r.won for r in recs) if full else None
            out[f"{self.prefix}_{n}_draws"] = sum(r.drawn for r in recs) if full else None
            out[f"{self.prefix}_{n}_losses"] = sum(r.lost for r in recs) if full else None
        return out


class GoalsCalculator(FeatureCalculator):
    """Goals for/against and goal-event counts over the last N games."""

    STATS = ("gf", "ga", "clean_sheets", "failed_to_score", "btts", "over25")

    def __init__(self, windows: tuple[int, ...], venue: bool | None = None) -> None:
        self.windows = windows
        self.venue = venue
        self.prefix = _venue_prefix(venue, "goals")

    def columns(self) -> list[str]:
        return [f"{self.prefix}_{n}_{s}" for n in self.windows for s in self.STATS]

    def compute(self, ctx: MatchContext) -> Features:
        out: Features = {}
        for n in self.windows:
            recs = ctx.history.last(n, venue=self.venue)
            full = len(recs) == n
            values = {
                "gf": sum(r.gf for r in recs),
                "ga": sum(r.ga for r in recs),
                "clean_sheets": sum(r.ga == 0 for r in recs),
                "failed_to_score": sum(r.gf == 0 for r in recs),
                "btts": sum(r.gf > 0 and r.ga > 0 for r in recs),
                "over25": sum(r.gf + r.ga > 2 for r in recs),
            }
            for stat in self.STATS:
                out[f"{self.prefix}_{n}_{stat}"] = values[stat] if full else None
        return out


class StreakCalculator(FeatureCalculator):
    """Length of current runs (wins, unbeaten, winless, losses, scoring, clean sheets)."""

    PREDICATES = {
        "streak_wins": lambda r: r.won,
        "streak_unbeaten": lambda r: not r.lost,
        "streak_winless": lambda r: not r.won,
        "streak_losses": lambda r: r.lost,
        "streak_scoring": lambda r: r.gf > 0,
        "streak_clean_sheets": lambda r: r.ga == 0,
    }

    def columns(self) -> list[str]:
        return list(self.PREDICATES)

    def compute(self, ctx: MatchContext) -> Features:
        recs = ctx.history.records
        if not recs:
            return dict.fromkeys(self.PREDICATES)
        return {name: _streak(recs, pred) for name, pred in self.PREDICATES.items()}


class SeasonCalculator(FeatureCalculator):
    """Season-to-date totals and per-game rates, split by venue."""

    def columns(self) -> list[str]:
        return ["season_pts", "season_ppg", "season_gf_pg", "season_ga_pg", "season_gd",
                "season_home_ppg", "season_away_ppg"]

    def compute(self, ctx: MatchContext) -> Features:
        recs = ctx.history.season(ctx.season_id)
        home = [r for r in recs if r.is_home]
        away = [r for r in recs if not r.is_home]
        pts = sum(r.points for r in recs)
        return {
            "season_pts": pts,
            "season_ppg": safe_div(pts, len(recs)),
            "season_gf_pg": safe_div(sum(r.gf for r in recs), len(recs)),
            "season_ga_pg": safe_div(sum(r.ga for r in recs), len(recs)),
            "season_gd": sum(r.gf - r.ga for r in recs),
            "season_home_ppg": safe_div(sum(r.points for r in home), len(home)),
            "season_away_ppg": safe_div(sum(r.points for r in away), len(away)),
        }


class TableCalculator(FeatureCalculator):
    """League position, band, gaps to the top and the drop, and last season's finish."""

    def __init__(self, cfg: FeatureConfig) -> None:
        self.cfg = cfg

    def columns(self) -> list[str]:
        return ["league_position", "position_band", "points_to_top", "points_above_relegation",
                "prev_season_position"]

    def compute(self, ctx: MatchContext) -> Features:
        table = ctx.table
        pts = table.row(ctx.team_id).points
        top = table.points_at(1)
        drop_pos = len(table.rows) - self.cfg.relegation_places + 1
        drop = table.points_at(drop_pos) if drop_pos > 0 else None
        return {
            "league_position": table.position(ctx.team_id),
            "position_band": ctx.state.band(ctx.team_id, ctx.season_id),
            "points_to_top": top - pts if top is not None else None,
            "points_above_relegation": pts - drop if drop is not None else None,
            "prev_season_position": ctx.state.previous_position(ctx.team_id, ctx.season_id),
        }


class StrengthCalculator(FeatureCalculator):
    """Elo rating and expectation, plus attack/defence strength relative to the league average."""

    def __init__(self, cfg: FeatureConfig) -> None:
        self.cfg = cfg

    def columns(self) -> list[str]:
        return ["elo", "elo_expected", "attack_strength", "defence_strength"]

    def compute(self, ctx: MatchContext) -> Features:
        row = ctx.table.row(ctx.team_id)
        league_avg = ctx.table.goals_per_team_game()
        enough = row.played >= self.cfg.min_games_for_strength and league_avg
        return {
            "elo": ctx.state.elo.rating(ctx.team_id),
            "elo_expected": ctx.state.elo.expected(ctx.team_id, ctx.opponent_id, ctx.is_home),
            "attack_strength": (row.gf / row.played) / league_avg if enough else None,
            "defence_strength": (row.ga / row.played) / league_avg if enough else None,
        }


class HeadToHeadCalculator(FeatureCalculator):
    """Recent record against this opponent, overall and at the same venue."""

    def __init__(self, last_n: int, venue_last_n: int) -> None:
        self.last_n = last_n
        self.venue_last_n = venue_last_n

    def columns(self) -> list[str]:
        return ["h2h_played", "h2h_pts", "h2h_wins", "h2h_draws", "h2h_losses", "h2h_gf", "h2h_ga",
                "h2h_prev_pts", "h2h_venue_played", "h2h_venue_pts", "h2h_venue_gf", "h2h_venue_ga"]

    def compute(self, ctx: MatchContext) -> Features:
        vs = lambda r: r.opponent_id == ctx.opponent_id  # noqa: E731
        recs = ctx.history.last(self.last_n, where=vs)
        venue = ctx.history.last(self.venue_last_n, venue=ctx.is_home, where=vs)
        has, has_venue = bool(recs), bool(venue)
        return {
            "h2h_played": len(recs),
            "h2h_pts": sum(r.points for r in recs) if has else None,
            "h2h_wins": sum(r.won for r in recs) if has else None,
            "h2h_draws": sum(r.drawn for r in recs) if has else None,
            "h2h_losses": sum(r.lost for r in recs) if has else None,
            "h2h_gf": sum(r.gf for r in recs) if has else None,
            "h2h_ga": sum(r.ga for r in recs) if has else None,
            "h2h_prev_pts": recs[-1].points if has else None,
            "h2h_venue_played": len(venue),
            "h2h_venue_pts": sum(r.points for r in venue) if has_venue else None,
            "h2h_venue_gf": sum(r.gf for r in venue) if has_venue else None,
            "h2h_venue_ga": sum(r.ga for r in venue) if has_venue else None,
        }


class SimilarOpponentCalculator(FeatureCalculator):
    """Record against teams that were in the opponent's current band at the time they were played."""

    def __init__(self, last_n: int) -> None:
        self.last_n = last_n

    def columns(self) -> list[str]:
        return ["opponent_band", "vs_band_played", "vs_band_ppg", "vs_band_gf_pg", "vs_band_ga_pg"]

    def compute(self, ctx: MatchContext) -> Features:
        band = ctx.state.band(ctx.opponent_id, ctx.season_id)
        recs = ctx.history.last(self.last_n, where=lambda r: r.opponent_band == band) if band else []
        n = len(recs)
        return {
            "opponent_band": band,
            "vs_band_played": n,
            "vs_band_ppg": safe_div(sum(r.points for r in recs), n),
            "vs_band_gf_pg": safe_div(sum(r.gf for r in recs), n),
            "vs_band_ga_pg": safe_div(sum(r.ga for r in recs), n),
        }


def default_calculators(cfg: FeatureConfig) -> list[FeatureCalculator]:
    """The standard calculator set used by the feature builder."""
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
        TableCalculator(cfg),
        StrengthCalculator(cfg),
        HeadToHeadCalculator(cfg.h2h_last_n, cfg.h2h_venue_last_n),
        SimilarOpponentCalculator(cfg.similar_opponent_last_n),
    ]
