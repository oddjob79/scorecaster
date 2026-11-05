"""Turn the wide odds columns of a results DataFrame into rows."""
from __future__ import annotations

from dataclasses import asdict

import pandas as pd

from scorecaster.ingest.fdcuk.columns import OddsColumn
from scorecaster.ingest.fdcuk.reader import to_numbers

ODDS_FIELDS = [
    "match_id",
    "bookmaker",
    "market",
    "selection",
    "line",
    "timing",
    "price",
]

# Handicap line columns per timing, newest name first.
# BbAHh is the Betbrain line, used up to 2018/19.
HANDICAP_LINE_COLUMNS = {
    "pre_match": ["AHh", "BbAHh"],
    "closing": ["AHCh"],
}
FIXED_LINES = {"1X2": 0.0, "OU": 2.5}


def build_odds_rows(
    results_df: pd.DataFrame, match_ids: list[int], label: str
) -> list[dict]:
    """Melt the stored bookmakers' odds into one row per price.

    `match_ids` gives the stored match for each row of `results_df`.
    Rows come back shaped like the odds table, e.g. match 101, pinnacle,
    1X2, home, line 0.0, closing, price 2.1. Empty prices, and handicap
    prices without a line, are left out.
    """
    odds_columns = [
        column
        for name in results_df.columns
        if (column := OddsColumn.parse(name))
    ]
    if not odds_columns:
        return []
    line_columns = [
        name
        for names in HANDICAP_LINE_COLUMNS.values()
        for name in names
        if name in results_df
    ]
    price_columns = [column.name for column in odds_columns]
    to_numbers(results_df, price_columns + line_columns, label)

    prices_df = _melt_prices(results_df, match_ids, odds_columns, line_columns)
    prices_df["line"] = _lines(prices_df)
    prices_df = prices_df.dropna(subset=["line"])
    return prices_df[ODDS_FIELDS].to_dict("records")


def _melt_prices(
    results_df: pd.DataFrame,
    match_ids: list[int],
    odds_columns: list[OddsColumn],
    line_columns: list[str],
) -> pd.DataFrame:
    """Return one row per non-empty price, labelled with its meaning."""
    price_columns = [column.name for column in odds_columns]
    wide_df = results_df[price_columns + line_columns]
    wide_df = wide_df.assign(match_id=match_ids)
    prices_df = wide_df.melt(
        id_vars=["match_id", *line_columns],
        var_name="name",
        value_name="price",
    )
    prices_df = prices_df.dropna(subset=["price"])
    meanings_df = pd.DataFrame([asdict(column) for column in odds_columns])
    return prices_df.merge(meanings_df, on="name")


def _lines(prices_df: pd.DataFrame) -> pd.Series:
    """Return each price's line.

    1X2 is 0 and over/under is 2.5. Asian handicap takes the file's
    handicap for the home side, and the opposite for the away side.
    """
    lines = prices_df["market"].map(FIXED_LINES)
    is_handicap = prices_df["market"] == "AH"
    for timing, names in HANDICAP_LINE_COLUMNS.items():
        present = [name for name in names if name in prices_df]
        if not present:
            continue
        home_handicap = prices_df[present].bfill(axis=1).iloc[:, 0]
        rows = is_handicap & (prices_df["timing"] == timing)
        lines[rows] = home_handicap[rows]
    away = is_handicap & (prices_df["selection"] == "away")
    lines[away] = 0.0 - lines[away]
    return lines
