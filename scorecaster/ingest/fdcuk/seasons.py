"""Describe a season by its label and the years it spans."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SeasonSpan:
    """A season's label and years.

    ``2024/25`` spans 2024 to 2025; ``2024`` is a single calendar year.
    """

    label: str
    start: int
    end: int

    @property
    def is_calendar_year(self) -> bool:
        """Return True for leagues that play January to December."""
        return self.start == self.end

    @classmethod
    def starting(cls, start: int) -> SeasonSpan:
        """Return the August–May season starting in `start`.

        2024 -> SeasonSpan('2024/25', 2024, 2025)
        """
        return cls(f"{start}/{(start + 1) % 100:02d}", start, start + 1)

    @classmethod
    def parse(cls, value: str) -> SeasonSpan:
        """Read an extra-league Season value.

        '2012/2013' -> SeasonSpan('2012/13', 2012, 2013)
        '2024' -> SeasonSpan('2024', 2024, 2024)
        """
        years = [int(part) for part in str(value).strip().split("/")]
        if len(years) == 1:
            return cls(str(years[0]), years[0], years[0])
        return cls.starting(years[0])
