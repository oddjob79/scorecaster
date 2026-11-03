"""Download football-data.co.uk CSVs into the downloads table, fetching each URL once."""
from __future__ import annotations

import logging
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Iterable

import requests
from sqlalchemy import select

from scorecaster.config import LeagueConfig
from scorecaster.db import Database, Download

log = logging.getLogger(__name__)

BASE_URL = "https://www.football-data.co.uk"
SECONDS_BETWEEN_FETCHES = 2.0


class RateLimiter:
    """Sliding-window limiter allowing `max_calls` per `period` seconds."""

    def __init__(self, max_calls: int, period: float = 60.0,
                 clock: Callable[[], float] = time.monotonic,
                 sleep: Callable[[float], None] = time.sleep) -> None:
        self.max_calls = max_calls
        self.period = period
        self._clock = clock
        self._sleep = sleep
        self._calls: deque[float] = deque()

    def wait(self) -> None:
        """Block until another call is permitted, then record it."""
        now = self._clock()
        while self._calls and now - self._calls[0] >= self.period:
            self._calls.popleft()
        if len(self._calls) >= self.max_calls:
            self._sleep(self.period - (now - self._calls[0]))
            self._calls.popleft()
        self._calls.append(self._clock())


@dataclass(frozen=True)
class CsvFile:
    """One football-data.co.uk CSV: a league-season file, or an all-seasons file when `season_start` is None."""

    league: LeagueConfig
    season_start: int | None
    url: str

    def is_live(self, current_season: int) -> bool:
        """Return True when the file can still change: the season in progress, or an all-seasons file."""
        return self.season_start is None or self.season_start == current_season


def season_dir(start_year: int) -> str:
    """Return the site's folder name for a season: 2024 -> '2425', 2099 -> '9900'."""
    return f"{start_year % 100:02d}{(start_year + 1) % 100:02d}"


def list_csv_files(leagues: Iterable[LeagueConfig], current_season: int) -> list[CsvFile]:
    """List every CSV the config covers: E0 from 2005 -> mmz4281/0506/E0.csv … ; BRA -> new/BRA.csv."""
    files: list[CsvFile] = []
    for league in leagues:
        if league.file_style == "season":
            for start in range(league.first_season, current_season + 1):
                files.append(CsvFile(league, start, f"{BASE_URL}/mmz4281/{season_dir(start)}/{league.code}.csv"))
        else:
            files.append(CsvFile(league, None, f"{BASE_URL}/new/{league.code}.csv"))
    return files


class DownloadCache:
    """Serve file bodies from `downloads`, fetching from the site only when a URL is missing or refreshed."""

    def __init__(self, db: Database, limiter: RateLimiter | None = None,
                 session: requests.Session | None = None, timeout: float = 30.0) -> None:
        self.db = db
        self.limiter = limiter or RateLimiter(1, SECONDS_BETWEEN_FETCHES)
        self.session = session or requests.Session()
        self.timeout = timeout

    def get(self, url: str, refresh: bool = False) -> bytes:
        """Return the body for `url`, from the cache unless `refresh` is set or nothing is stored yet."""
        with self.db.session() as s:
            row = s.scalar(select(Download).where(Download.url == url))
            if row is not None and not refresh:
                log.info("cached  %s (%d bytes)", url, len(row.body))
                return row.body
            body = self._fetch(url)
            if row is None:
                row = Download(url=url)
                s.add(row)
            row.body = body
            row.fetched_at = datetime.now(timezone.utc)
            log.info("fetched %s (%d bytes)", url, len(body))
            return body

    def _fetch(self, url: str) -> bytes:
        self.limiter.wait()
        resp = self.session.get(url, timeout=self.timeout)
        resp.raise_for_status()
        return resp.content
