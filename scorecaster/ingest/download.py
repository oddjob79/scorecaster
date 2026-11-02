"""Rate limiting for football-data.co.uk downloads."""
from __future__ import annotations

import time
from collections import deque
from typing import Callable


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
