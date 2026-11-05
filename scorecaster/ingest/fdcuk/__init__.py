"""Load football-data.co.uk CSVs into the database.

The package is split by job:

- ``files``    which CSV files exist and where
- ``columns``  what each CSV column means
- ``reader``   bytes -> one clean DataFrame per file
- ``seasons``  season labels such as ``2024/25`` and ``2024``
- ``odds``     wide odds columns -> one row per price
- ``loader``   DataFrames -> seasons, teams, matches and odds tables
"""
from scorecaster.ingest.fdcuk.loader import CsvLoader

__all__ = ["CsvLoader"]
