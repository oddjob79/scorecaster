"""Fetch files over HTTP once, keeping each body in the downloads table."""
from __future__ import annotations

import logging
import time
from collections import deque
from datetime import datetime, timezone
from typing import Callable

import requests
from sqlalchemy import select

from scorecaster.db import Database, Download

log = logging.getLogger(__name__)

SECONDS_BETWEEN_FETCHES = 2.0


class RateLimiter:
    """Allow at most `max_calls` calls in any `period` seconds."""

    def __init__(
        self,
        max_calls: int,
        period: float = 60.0,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.max_calls = max_calls
        self.period = period
        self._clock = clock
        self._sleep = sleep
        self._calls: deque[float] = deque()

    def wait(self) -> None:
        """Block until another call is allowed, then record it."""
        now = self._clock()
        while self._calls and now - self._calls[0] >= self.period:
            self._calls.popleft()
        if len(self._calls) >= self.max_calls:
            self._sleep(self.period - (now - self._calls[0]))
            self._calls.popleft()
        self._calls.append(self._clock())


class DownloadCache:
    """Serve file bodies from the database, fetching each URL only once.

    Requests are spaced by a rate limiter so a full first load doesn't
    hammer the site. `refresh` re-fetches a file that can still change.
    """

    def __init__(
        self,
        db: Database,
        limiter: RateLimiter | None = None,
        session: requests.Session | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.db = db
        self.limiter = limiter or RateLimiter(1, SECONDS_BETWEEN_FETCHES)
        self.session = session or requests.Session()
        self.timeout = timeout

    def get(self, url: str) -> bytes:
        """Return the stored body for `url`, fetching it if not stored."""
        body = self._stored_body(url)
        if body is not None:
            log.info("cached  %s (%d bytes)", url, len(body))
            return body
        return self.refresh(url)

    def refresh(self, url: str) -> bytes:
        """Fetch `url` from the site, store the body and return it."""
        body = self._fetch(url)
        self._store(url, body)
        log.info("fetched %s (%d bytes)", url, len(body))
        return body

    def _stored_body(self, url: str) -> bytes | None:
        """Return the stored body for `url`, or None if there isn't one."""
        with self.db.session() as session:
            return session.scalar(
                select(Download.body).where(Download.url == url)
            )

    def _store(self, url: str, body: bytes) -> None:
        """Save a body for `url`, replacing any earlier copy."""
        with self.db.session() as session:
            row = session.scalar(select(Download).where(Download.url == url))
            if row is None:
                row = Download(url=url)
                session.add(row)
            row.body = body
            row.fetched_at = datetime.now(timezone.utc)

    def _fetch(self, url: str) -> bytes:
        """Download `url`, raising for any HTTP error such as a 404."""
        self.limiter.wait()
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        return response.content
