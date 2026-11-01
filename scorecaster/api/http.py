"""HTTP transport: rate limiting, requests client and a database-backed cache."""
from __future__ import annotations

import json
import time
from collections import deque
from datetime import datetime, timezone
from typing import Any, Callable

import requests
from sqlalchemy import select

from scorecaster.api.base import ApiError, JsonClient
from scorecaster.db import ApiResponse, Database


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


class HttpJsonClient(JsonClient):
    """Rate-limited requests client for token-authenticated JSON APIs."""

    def __init__(self, base_url: str, headers: dict[str, str], limiter: RateLimiter,
                 session: requests.Session | None = None, max_retries: int = 3, timeout: float = 30.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.limiter = limiter
        self.session = session or requests.Session()
        self.session.headers.update(headers)
        self.max_retries = max_retries
        self.timeout = timeout

    def get(self, path: str, params: dict[str, Any] | None = None, refresh: bool = False) -> dict:
        """GET a path, retrying on HTTP 429 using the server's back-off hint."""
        for _ in range(self.max_retries + 1):
            self.limiter.wait()
            resp = self.session.get(f"{self.base_url}/{path.lstrip('/')}", params=params, timeout=self.timeout)
            if resp.status_code == 429:
                time.sleep(float(resp.headers.get("X-RequestCounter-Reset", resp.headers.get("Retry-After", 60))))
                continue
            if resp.status_code != 200:
                raise ApiError(resp.status_code, resp.text[:300])
            return resp.json()
        raise ApiError(429, "rate limit retries exhausted")


class CachedJsonClient(JsonClient):
    """Decorator that stores every response in `api_responses` and serves repeats from it."""

    def __init__(self, inner: JsonClient, db: Database) -> None:
        self.inner = inner
        self.db = db

    @staticmethod
    def _key(params: dict[str, Any] | None) -> str:
        return json.dumps(params or {}, sort_keys=True)

    def get(self, path: str, params: dict[str, Any] | None = None, refresh: bool = False) -> dict:
        """Return a cached body unless `refresh` is set or nothing is cached yet."""
        key = self._key(params)
        with self.db.session() as s:
            row = s.scalar(select(ApiResponse).where(ApiResponse.path == path, ApiResponse.params == key))
            if row is not None and not refresh:
                return json.loads(row.body)
            body = self.inner.get(path, params)
            if row is None:
                row = ApiResponse(path=path, params=key)
                s.add(row)
            row.body = json.dumps(body)
            row.fetched_at = datetime.now(timezone.utc).replace(tzinfo=None)
            return body
