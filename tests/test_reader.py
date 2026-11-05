"""Reading football-data.co.uk CSVs, including the source's quirks."""
import logging

import pandas as pd
import pytest

from scorecaster.ingest.fdcuk.reader import (
    decode_csv,
    parse_dates,
    read_results,
)

HEADER = "Div,Date,HomeTeam,AwayTeam,FTHG,FTAG,FTR,HS"


def csv_bytes(*lines: str) -> bytes:
    """Return a CSV body made of a header and data lines."""
    return ("\n".join([HEADER, *lines]) + "\n").encode("utf-8")


def test_decode_csv_drops_byte_order_mark():
    assert decode_csv("﻿Div,Date".encode("utf-8")) == "Div,Date"


def test_decode_csv_falls_back_to_cp1252():
    assert decode_csv("Mönchengladbach".encode("cp1252")) == (
        "Mönchengladbach"
    )


def test_parse_dates_reads_two_and_four_digit_years():
    parsed = parse_dates(pd.Series(["10/08/24", "10/08/2024", "junk"]))
    assert list(parsed[:2]) == [pd.Timestamp("2024-08-10").date()] * 2
    assert pd.isna(parsed[2])


def test_read_results_trims_empty_extra_fields():
    body = csv_bytes("E0,10/08/24,Ashford,Bexley,2,1,H,12,,,")
    results_df = read_results(body, "test")
    assert len(results_df) == 1
    assert results_df["HS"].iloc[0] == 12


def test_read_results_drops_rows_whose_extra_fields_hold_data(caplog):
    body = csv_bytes(
        "E0,10/08/24,Ashford,Bexley,2,1,H,12",
        "E0,11/08/24,Crawley,Dartford,0,3,A,8,,Crawley,1,1,Abandoned",
    )
    with caplog.at_level(logging.WARNING):
        results_df = read_results(body, "test")
    assert list(results_df["HomeTeam"]) == ["Ashford"]
    assert "dropped row with extra data" in caplog.text


def test_read_results_empties_junk_numbers_and_warns(caplog):
    body = csv_bytes("E0,10/08/24,Ashford,Bexley,2,1,H,x")
    with caplog.at_level(logging.WARNING):
        results_df = read_results(body, "test")
    assert pd.isna(results_df["HS"].iloc[0])
    assert "HS='x' is not a number" in caplog.text


def test_read_results_drops_rows_with_unreadable_dates(caplog):
    body = csv_bytes(
        "E0,10/08/24,Ashford,Bexley,2,1,H,12",
        "E0,someday,Crawley,Dartford,0,0,D,8",
    )
    with caplog.at_level(logging.WARNING):
        results_df = read_results(body, "test")
    assert len(results_df) == 1
    assert "unreadable date" in caplog.text


def test_read_results_renames_older_and_extra_league_columns():
    body = (
        "Country,Season,Date,Home,Away,HG,AG,Res,Unnamed\n"
        "Brazil,2024,13/04/2024,Rio,Santos,0,1,A,\n"
    ).encode("utf-8")
    results_df = read_results(body, "test")
    for column in ("HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR"):
        assert column in results_df


def test_read_results_keeps_quoted_commas_in_one_field():
    body = (
        'Date,HomeTeam,AwayTeam,BbAHh\n'
        '10/08/24,Ashford,Bexley,"-0.5,-1"\n'
    ).encode("utf-8")
    results_df = read_results(body, "test")
    assert results_df["BbAHh"].iloc[0] == "-0.5,-1"


def test_read_results_drops_columns_with_an_empty_header():
    body = (
        "Date,HomeTeam,AwayTeam,,FTHG,\n"
        "10/08/24,Ashford,Bexley,junk,2,more junk\n"
    ).encode("utf-8")
    results_df = read_results(body, "test")
    assert list(results_df.columns) == [
        "Date", "HomeTeam", "AwayTeam", "FTHG"
    ]
    assert results_df["FTHG"].iloc[0] == 2


def test_read_results_suffixes_repeated_column_names():
    body = (
        "Date,HomeTeam,AwayTeam,HS,HS\n"
        "10/08/24,Ashford,Bexley,12,99\n"
    ).encode("utf-8")
    results_df = read_results(body, "test")
    assert results_df["HS"].iloc[0] == 12
    assert results_df["HS.1"].iloc[0] == "99"


def test_read_results_rejects_an_empty_file():
    with pytest.raises(ValueError, match="the file is empty"):
        read_results(b"", "test")
