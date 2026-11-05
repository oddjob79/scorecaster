"""Read a football-data.co.uk CSV into one clean DataFrame."""
from __future__ import annotations

import csv
import io
import logging

import pandas as pd

from scorecaster.ingest.fdcuk.columns import (
    NUMBER_COLUMNS,
    RENAMED_COLUMNS,
    REQUIRED_COLUMNS,
)

log = logging.getLogger(__name__)


def read_results(body: bytes, label: str) -> pd.DataFrame:
    """Read a CSV body into one row per match, in one consistent shape.

    The files vary by season: encodings differ, some rows carry extra
    fields, older files use two-digit years and other column names. The
    result always has the modern column names, ``Date`` as dates, ``Time``
    as times and the result and stats columns as numbers. Problems are
    logged against `label`.
    """
    results_df = _parse_csv(decode_csv(body), label)
    results_df = results_df.rename(columns=RENAMED_COLUMNS)
    results_df = results_df.dropna(subset=REQUIRED_COLUMNS)
    results_df = _drop_bad_dates(results_df, label)
    if "Time" in results_df:
        results_df["Time"] = parse_times(results_df["Time"])
    number_columns = [name for name in NUMBER_COLUMNS if name in results_df]
    to_numbers(results_df, number_columns, label)
    return results_df


def decode_csv(body: bytes) -> str:
    """Decode as UTF-8 without its byte-order mark, or as older cp1252."""
    try:
        return body.decode("utf-8-sig")
    except UnicodeDecodeError:
        return body.decode("cp1252")


def parse_dates(raw: pd.Series) -> pd.Series:
    """Parse ``dd/mm/yy`` and ``dd/mm/yyyy`` dates in one column.

    '10/08/24' and '10/08/2024' -> 2024-08-10
    """
    text = raw.astype(str).str.strip()
    four_digit_years = pd.to_datetime(
        text.where(text.str.len() == 10), format="%d/%m/%Y", errors="coerce"
    )
    two_digit_years = pd.to_datetime(
        text.where(text.str.len() == 8), format="%d/%m/%y", errors="coerce"
    )
    return four_digit_years.fillna(two_digit_years).dt.date


def parse_times(raw: pd.Series) -> pd.Series:
    """Parse ``HH:MM`` kick-off times, leaving blanks and junk empty."""
    return pd.to_datetime(raw, format="%H:%M", errors="coerce").dt.time


def to_numbers(
    results_df: pd.DataFrame, columns: list[str], label: str
) -> None:
    """Convert columns to numbers in place, logging values that aren't."""
    for name in columns:
        converted = pd.to_numeric(results_df[name], errors="coerce")
        failed = results_df[name].notna() & converted.isna()
        for row, value in results_df.loc[failed, name].items():
            log.warning(
                "%s row %s: %s=%r is not a number", label, row, name, value
            )
        results_df[name] = converted


def _parse_csv(text: str, label: str) -> pd.DataFrame:
    """Parse CSV text into string columns, empty values as missing.

    Rows are read with the csv module so every row gets the same rule
    wherever it sits: blank lines are skipped, short rows padded, and
    long rows trimmed or dropped by `_trim_extra_fields`. Columns with
    an empty header are dropped.
    """
    rows = csv.reader(io.StringIO(text))
    header = next(rows)
    width = len(header)
    records = []
    for fields in rows:
        if not any(field.strip() for field in fields):
            continue
        if len(fields) > width:
            fields = _trim_extra_fields(fields, width, label)
            if fields is None:
                continue
        records.append(fields + [""] * (width - len(fields)))
    results_df = pd.DataFrame(records, columns=header, dtype=object)
    results_df = results_df.mask(results_df == "")
    named = [name for name in header if name.strip()]
    return results_df[named]


def _trim_extra_fields(
    fields: list[str], width: int, label: str
) -> list[str] | None:
    """Cut a too-long row back to the header width, or skip it.

    Some files end rows with empty extra fields (SP2 2007/08 rows end
    ``,,,``), which are safe to drop. Extras holding data, such as an
    abandoned-match note, can't be placed in a column, so the row is
    logged and skipped.
    """
    extras = fields[width:]
    if all(not field.strip() for field in extras):
        return fields[:width]
    log.warning("%s: dropped row with extra data: %s", label, ",".join(fields))
    return None


def _drop_bad_dates(results_df: pd.DataFrame, label: str) -> pd.DataFrame:
    """Parse the Date column, logging and dropping unreadable rows."""
    results_df["Date"] = parse_dates(results_df["Date"])
    unreadable = results_df["Date"].isna()
    for row in results_df.index[unreadable]:
        log.warning("%s row %s: unreadable date", label, row)
    return results_df[~unreadable].copy()
