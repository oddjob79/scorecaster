"""In-memory league state replayed chronologically to derive leak-free pre-match features."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from typing import Callable, Iterable

from scorecaster.config import FeatureConfig
from scorecaster.db import Match


@dataclass(frozen=True)
class TeamMatchRecord:
    """One finished match from a single team's perspective."""

    match_id: int
    day: date
    season_id: int
    is_home: bool
    opponent_id: int
    gf: int
    ga: int
    opponent_band: int | None

    @property
    def points(self) -> int:
        return 3 if self.gf > self.ga else 1 if self.gf == self.ga else 0

    @property
    def won(self) -> bool:
        return self.gf > self.ga

    @property
    def drawn(self) -> bool:
        return self.gf == self.ga

    @property
    def lost(self) -> bool:
        return self.gf < self.ga


class TeamHistory:
    """Chronological list of a team's finished matches."""

    def __init__(self) -> None:
        self.records: list[TeamMatchRecord] = []

    def __len__(self) -> int:
        return len(self.records)

    def add(self, record: TeamMatchRecord) -> None:
        self.records.append(record)

    def last(self, n: int | None = None, venue: bool | None = None,
             where: Callable[[TeamMatchRecord], bool] | None = None) -> list[TeamMatchRecord]:
        """Most recent `n` matching records (oldest first); `venue` True=home, False=away."""
        out: list[TeamMatchRecord] = []
        for rec in reversed(self.records):
            if venue is not None and rec.is_home != venue:
                continue
            if where is not None and not where(rec):
                continue
            out.append(rec)
            if n is not None and len(out) == n:
                break
        return out[::-1]

    def season(self, season_id: int) -> list[TeamMatchRecord]:
        return [r for r in self.records if r.season_id == season_id]


@dataclass
class TableRow:
    """Cumulative league-table line for a team."""

    team_id: int
    played: int = 0
    won: int = 0
    drawn: int = 0
    lost: int = 0
    gf: int = 0
    ga: int = 0

    @property
    def points(self) -> int:
        return self.won * 3 + self.drawn

    @property
    def gd(self) -> int:
        return self.gf - self.ga

    def add(self, gf: int, ga: int) -> None:
        self.played += 1
        self.gf += gf
        self.ga += ga
        if gf > ga:
            self.won += 1
        elif gf == ga:
            self.drawn += 1
        else:
            self.lost += 1


class LeagueTable:
    """League table reconstructed from results (points, goal difference, goals scored)."""

    def __init__(self, team_ids: Iterable[int] = ()) -> None:
        self.rows: dict[int, TableRow] = {t: TableRow(t) for t in team_ids}

    def row(self, team_id: int) -> TableRow:
        return self.rows.setdefault(team_id, TableRow(team_id))

    def apply(self, home_id: int, away_id: int, home_goals: int, away_goals: int) -> None:
        self.row(home_id).add(home_goals, away_goals)
        self.row(away_id).add(away_goals, home_goals)

    def standings(self) -> list[TableRow]:
        return sorted(self.rows.values(), key=lambda r: (-r.points, -r.gd, -r.gf, r.team_id))

    def position(self, team_id: int) -> int | None:
        """1-based position, or None if the team has not played yet."""
        if self.row(team_id).played == 0:
            return None
        return next(i for i, r in enumerate(self.standings(), 1) if r.team_id == team_id)

    def final_position(self, team_id: int) -> int | None:
        return self.position(team_id) if team_id in self.rows else None

    def points_at(self, position: int) -> int | None:
        table = self.standings()
        return table[position - 1].points if 0 < position <= len(table) else None

    def goals_per_team_game(self) -> float | None:
        played = sum(r.played for r in self.rows.values())
        return sum(r.gf for r in self.rows.values()) / played if played else None


class PositionBands:
    """Maps league positions to fixed band numbers (1 = top band)."""

    def __init__(self, bands: tuple[tuple[int, int], ...]) -> None:
        self.bands = bands

    @property
    def bottom(self) -> int:
        return len(self.bands)

    def band_of(self, position: int | None) -> int | None:
        if position is None:
            return None
        for i, (lo, hi) in enumerate(self.bands, 1):
            if lo <= position <= hi:
                return i
        return self.bottom


class EloRatings:
    """Goal-difference-weighted Elo with home advantage and between-season regression."""

    def __init__(self, cfg: FeatureConfig) -> None:
        self.cfg = cfg
        self.ratings: dict[int, float] = {}

    def rating(self, team_id: int) -> float:
        return self.ratings.setdefault(team_id, self.cfg.elo_initial)

    def expected(self, team_id: int, opponent_id: int, is_home: bool) -> float:
        """Expected score (0-1) for `team_id` against `opponent_id`."""
        adv = self.cfg.elo_home_advantage if is_home else -self.cfg.elo_home_advantage
        diff = self.rating(team_id) + adv - self.rating(opponent_id)
        return 1.0 / (1.0 + 10 ** (-diff / 400.0))

    def update(self, home_id: int, away_id: int, home_goals: int, away_goals: int) -> None:
        exp = self.expected(home_id, away_id, True)
        actual = 1.0 if home_goals > away_goals else 0.5 if home_goals == away_goals else 0.0
        margin = abs(home_goals - away_goals)
        mult = 1.0 if margin <= 1 else 1.5 if margin == 2 else (11 + margin) / 8
        delta = self.cfg.elo_k * mult * (actual - exp)
        self.ratings[home_id] = self.rating(home_id) + delta
        self.ratings[away_id] = self.rating(away_id) - delta

    def new_season(self, team_ids: Iterable[int], relegation_places: int) -> None:
        """Regress known teams toward the mean; newcomers start at the average of the lowest-rated teams."""
        known = sorted(self.ratings.values())
        newcomer = sum(known[:relegation_places]) / min(len(known), relegation_places) if known else self.cfg.elo_initial
        mean = sum(known) / len(known) if known else self.cfg.elo_initial
        for team_id, r in list(self.ratings.items()):
            self.ratings[team_id] = r + self.cfg.elo_season_regression * (mean - r)
        for team_id in team_ids:
            self.ratings.setdefault(team_id, newcomer)


class LeagueState:
    """Aggregates histories, tables and ratings; updated only after a day's features are taken."""

    def __init__(self, cfg: FeatureConfig, season_teams: dict[int, set[int]], previous_season: dict[int, int | None]) -> None:
        self.cfg = cfg
        self.bands = PositionBands(cfg.position_bands)
        self.season_teams = season_teams
        self.previous_season = previous_season
        self.histories: dict[int, TeamHistory] = defaultdict(TeamHistory)
        self.tables: dict[int, LeagueTable] = {}
        self.elo = EloRatings(cfg)

    def table(self, season_id: int) -> LeagueTable:
        """Table for a season, starting the season (and Elo regression) on first access."""
        if season_id not in self.tables:
            teams = self.season_teams.get(season_id, set())
            if self.tables:
                self.elo.new_season(teams, self.cfg.relegation_places)
            self.tables[season_id] = LeagueTable(teams)
        return self.tables[season_id]

    def previous_table(self, season_id: int) -> LeagueTable | None:
        prev = self.previous_season.get(season_id)
        return self.tables.get(prev) if prev is not None else None

    def previous_position(self, team_id: int, season_id: int) -> int | None:
        prev = self.previous_table(season_id)
        return prev.final_position(team_id) if prev else None

    def band(self, team_id: int, season_id: int) -> int | None:
        """Current band; before a team's first game, last season's band (promoted teams: bottom band)."""
        position = self.table(season_id).position(team_id)
        if position is not None:
            return self.bands.band_of(position)
        prev = self.previous_table(season_id)
        if prev is None:
            return None
        return self.bands.band_of(prev.final_position(team_id)) or self.bands.bottom

    def start_day(self, matches: list[Match]) -> None:
        """Open any seasons first seen on this day so season-start adjustments precede features."""
        for season_id in dict.fromkeys(m.season_id for m in matches):
            self.table(season_id)

    def apply_day(self, matches: list[Match]) -> None:
        """Apply a day's finished results after snapshotting pre-match bands."""
        finished = [m for m in matches if m.is_finished]
        bands = {(m.id, t): self.band(t, m.season_id) for m in finished for t in (m.home_team_id, m.away_team_id)}
        for m in finished:
            day = m.utc_date.date()
            for team, opp, gf, ga, home in ((m.home_team_id, m.away_team_id, m.ft_home, m.ft_away, True),
                                            (m.away_team_id, m.home_team_id, m.ft_away, m.ft_home, False)):
                self.histories[team].add(TeamMatchRecord(m.id, day, m.season_id, home, opp, gf, ga, bands[(m.id, opp)]))
            self.table(m.season_id).apply(m.home_team_id, m.away_team_id, m.ft_home, m.ft_away)
            self.elo.update(m.home_team_id, m.away_team_id, m.ft_home, m.ft_away)


@dataclass(frozen=True)
class MatchContext:
    """A match viewed from one team's side, with read access to pre-match state."""

    match: Match
    team_id: int
    opponent_id: int
    is_home: bool
    state: LeagueState

    @classmethod
    def for_side(cls, match: Match, is_home: bool, state: LeagueState) -> "MatchContext":
        team, opp = (match.home_team_id, match.away_team_id) if is_home else (match.away_team_id, match.home_team_id)
        return cls(match, team, opp, is_home, state)

    @property
    def day(self) -> date:
        return self.match.utc_date.date()

    @property
    def season_id(self) -> int:
        return self.match.season_id

    @property
    def history(self) -> TeamHistory:
        return self.state.histories[self.team_id]

    @property
    def table(self) -> LeagueTable:
        return self.state.table(self.season_id)


def safe_div(a: float, b: float) -> float | None:
    """Division returning None when the denominator is zero."""
    return a / b if b else None

