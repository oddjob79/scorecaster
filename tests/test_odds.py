"""Decoding odds column names and melting them into price rows."""
import pandas as pd
import pytest

from scorecaster.ingest.fdcuk.columns import OddsColumn, unknown_columns
from scorecaster.ingest.fdcuk.odds import build_odds_rows


@pytest.mark.parametrize(
    "name, expected",
    [
        ("PSCH", ("pinnacle", "closing", "1X2", "home")),
        ("PSD", ("pinnacle", "pre_match", "1X2", "draw")),
        ("P>2.5", ("pinnacle", "pre_match", "OU", "over")),
        ("PCAHA", ("pinnacle", "closing", "AH", "away")),
        ("BbAv<2.5", ("market_avg", "pre_match", "OU", "under")),
        ("MaxCAHH", ("market_max", "closing", "AH", "home")),
        ("BFECA", ("betfair_exchange", "closing", "1X2", "away")),
        ("B365H", ("bet365", "pre_match", "1X2", "home")),
    ],
)
def test_odds_column_decodes_stored_bookmakers(name, expected):
    column = OddsColumn.parse(name)
    assert (
        column.bookmaker, column.timing, column.market, column.selection
    ) == expected


@pytest.mark.parametrize("name", ["WHH", "PPCA", "HS", "AHh", "BbAH"])
def test_odds_column_ignores_other_columns(name):
    assert OddsColumn.parse(name) is None


def test_unknown_columns_lists_only_new_columns():
    columns = ["Div", "HS", "PSCH", "WHH", "BbAHh", "HxG", "Weather"]
    assert unknown_columns(columns) == ["Weather"]


def odds_rows(columns: dict) -> list[dict]:
    """Build price rows for one match from {column: value}."""
    results_df = pd.DataFrame(
        {name: [value] for name, value in columns.items()}
    )
    return build_odds_rows(results_df, [7], "test")


def test_lines_are_zero_for_1x2_and_2_5_for_over_under():
    rows = odds_rows({"PSH": "2.1", "Avg>2.5": "1.9"})
    lines = {row["market"]: row["line"] for row in rows}
    assert lines == {"1X2": 0.0, "OU": 2.5}


def test_asian_handicap_away_takes_the_opposite_line():
    rows = odds_rows({
        "AHh": "-0.75", "AvgAHH": "1.95", "AvgAHA": "1.90",
        "AHCh": "-1", "PCAHH": "2.0",
    })
    lines = {(row["selection"], row["timing"]): row["line"] for row in rows}
    assert lines == {
        ("home", "pre_match"): -0.75,
        ("away", "pre_match"): 0.75,
        ("home", "closing"): -1.0,
    }


def test_handicap_prices_without_a_readable_line_are_dropped():
    rows = odds_rows({"BbAHh": "-0.5,-1", "BbAvAHH": "1.9", "PSH": "2.0"})
    assert [row["market"] for row in rows] == ["1X2"]


def test_empty_prices_are_dropped_and_rows_carry_the_match_id():
    rows = odds_rows({"PSH": "2.1", "PSD": None, "PSA": "3.5"})
    assert {row["selection"] for row in rows} == {"home", "away"}
    assert {row["match_id"] for row in rows} == {7}
