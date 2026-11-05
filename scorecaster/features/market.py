"""Turn bookmaker prices into probabilities with the margin removed."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MarketProbabilities:
    """The market's pre-match view of one match, from the home side.

    A value is None when the market's prices for it are missing.
    """

    home: float | None = None
    draw: float | None = None
    away: float | None = None
    over_2_5: float | None = None


def remove_margin(prices: list[float | None]) -> list[float | None]:
    """Return fair probabilities for a complete set of prices.

    Each 1/price is divided by the sum of all of them, which removes the
    bookmaker's margin: 2.00 / 3.50 / 4.00 -> 0.48, 0.27, 0.24. If any
    price is missing, every probability is None.
    """
    if any(price is None or price <= 1 for price in prices):
        return [None] * len(prices)
    implied = [1 / price for price in prices]
    total = sum(implied)
    return [value / total for value in implied]


def market_probabilities(
    home: float | None,
    draw: float | None,
    away: float | None,
    over: float | None,
    under: float | None,
) -> MarketProbabilities:
    """Return a match's 1X2 and over-2.5 probabilities from its prices."""
    home_p, draw_p, away_p = remove_margin([home, draw, away])
    over_p, _ = remove_margin([over, under])
    return MarketProbabilities(home_p, draw_p, away_p, over_p)
