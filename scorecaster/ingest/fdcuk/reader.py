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

    Rows are read one at a time with the csv module (quoted commas stay
    in one field) and fitted to the header by `_fit_row`, so every row
    follows the same rule wherever it sits. Columns with an empty header
    are left out; repeated names get a suffix ('Time', 'Time.1').
    """
    rows = csv.reader(io.StringIO(text))
    header = next(rows, None)
    if header is None:
        raise ValueError(f"{label}: the file is empty")
    kept = [i for i, name in enumerate(header) if name.strip()]
    names = _unique_names([header[i] for i in kept])

    records = []
    for fields in rows:
        fitted = _fit_row(fields, len(header), label)
        if fitted is not None:
            records.append([fitted[i] for i in kept])
    results_df = pd.DataFrame(records, columns=names, dtype=object)
    return results_df.mask(results_df == "")


def _fit_row(
    fields: list[str], width: int, label: str
) -> list[str] | None:
    """Return a row fitted to the header width, or None to skip it.

    Blank rows are skipped. Short rows are padded with empty fields.
    Long rows lose their extra fields if those are empty (SP2 2007/08
    rows end ``,,,``); if any holds data, such as an abandoned-match
    note, the row can't be placed in columns, so it is logged and
    skipped.
    """
    if not any(field.strip() for field in fields):
        return None
    extras = fields[width:]
    if any(field.strip() for field in extras):
        log.warning(
            "%s: dropped row with extra data: %s", label, ",".join(fields)
        )
        return None
    return fields[:width] + [""] * (width - len(fields))


def _unique_names(names: list[str]) -> list[str]:
    """Suffix repeated names: ['Time', 'Time'] -> ['Time', 'Time.1']."""
    seen: dict[str, int] = {}
    unique = []
    for name in names:
        count = seen.get(name, 0)
        seen[name] = count + 1
        unique.append(f"{name}.{count}" if count else name)
    return unique


def _drop_bad_dates(results_df: pd.DataFrame, label: str) -> pd.DataFrame:
    """Parse the Date column, logging and dropping unreadable rows."""
    results_df["Date"] = parse_dates(results_df["Date"])
    unreadable = results_df["Date"].isna()
    for row in results_df.index[unreadable]:
        log.warning("%s row %s: unreadable date", label, row)
    return results_df[~unreadable].copy()
