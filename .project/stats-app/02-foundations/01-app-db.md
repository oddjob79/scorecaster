# 01 App database (plan)

## Goal

`scripts/build_app_db.py` writes `data/app.db`: a read-only reporting copy of `data/scorecaster.db`, cut down to what the stats app shows. The API reads only this file.

## Depends on

Phase 01 of scorecaster (the full database and feature table).

## Scope of the copy

| Table | Rows copied | Expected count (9 Nov 2026) |
|---|---|---|
| `competitions` | England, Scotland, Germany, Spain, Italy, France, Netherlands, Portugal, Belgium | 20 |
| `seasons` | those competitions, `start_year >= 2016` | 220 |
| `matches` | those seasons, status `finished` or `scheduled` (the one `void` match is left out) | 72,944 |
| `teams` | teams playing in those matches | 506 |
| `team_match_features` | rows for those matches, every column as-is | 145,888 |
| `odds` | `market_avg` rows for those matches: all markets and timings | 868,947 |

Left out: `downloads` and `team_aliases`. The API never reads them.

## Files that change

- `scorecaster/db/app_copy.py` (new): `AppDatabaseBuilder`, which builds the copy. It's importable, so the phase's tests chunk can exercise it, following the `FeatureBuilder` / `build_features.py` pattern. It uses the standard library's `sqlite3` only.
- `scripts/build_app_db.py` (new): parses no options, calls the builder, prints row counts and file size.

## Order of work

1. Build into `data/app.db.tmp`, deleting any leftover one first; the copy is always rebuilt from scratch.
2. Attach the source read-only.
3. Create the six tables and their indexes from the source's own `CREATE TABLE` and `CREATE INDEX` statements (`src.sqlite_master`), so every column and index matches the source exactly.
4. Copy each table with one `INSERT … SELECT`, filtered as in the scope table, in this order: competitions, seasons, matches, teams, features, odds. Each table's filter reads the rows already copied into the one before it. Teams come after matches because they're chosen by the matches. Foreign keys are checked once, in step 5, not row by row.
5. Run `PRAGMA integrity_check` and `PRAGMA foreign_key_check`. If either finds a problem, print it, stop, and leave the old `app.db` untouched.
6. Rename `app.db.tmp` over `app.db`. The rename is atomic, so a running API sees either the old file or the new one, never a half-built one.
7. Print the row count per table and the file size.

## Code outline

Signatures, docstrings and the SQL; function bodies are left out.

```python
# scorecaster/db/app_copy.py
"""Build the stats app's read-only copy of the database.

The copy holds the competitions, seasons, matches, teams, features and
market-average odds the stats app shows, with ids unchanged. It is built
beside the target file and swapped in only after it passes its checks.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

APP_COUNTRIES = (
    "England", "Scotland", "Germany", "Spain", "Italy",
    "France", "Netherlands", "Portugal", "Belgium",
)
FIRST_SEASON = 2016
APP_STATUSES = ("finished", "scheduled")
APP_BOOKMAKER = "market_avg"


class AppDatabaseError(Exception):
    """Raised when the built copy fails its integrity or key checks."""


@dataclass(frozen=True)
class TableCopy:
    """One table to copy: its name and the SELECT that picks its rows."""

    table: str
    select: str


# Parents before the tables that filter on them. Each SELECT reads the
# source (src) and the rows already copied into the new file (main).
TABLE_COPIES = (
    TableCopy(
        "competitions",
        "SELECT * FROM src.competitions WHERE country IN ({countries})",
    ),
    TableCopy(
        "seasons",
        "SELECT * FROM src.seasons"
        " WHERE competition_id IN (SELECT id FROM main.competitions)"
        " AND start_year >= :first_season",
    ),
    TableCopy(
        "matches",
        "SELECT * FROM src.matches"
        " WHERE season_id IN (SELECT id FROM main.seasons)"
        " AND status IN ({statuses})",
    ),
    TableCopy(
        "teams",
        "SELECT * FROM src.teams WHERE id IN ("
        " SELECT home_team_id FROM main.matches"
        " UNION SELECT away_team_id FROM main.matches)",
    ),
    TableCopy(
        "team_match_features",
        "SELECT * FROM src.team_match_features"
        " WHERE match_id IN (SELECT id FROM main.matches)",
    ),
    TableCopy(
        "odds",
        "SELECT * FROM src.odds WHERE bookmaker = :bookmaker"
        " AND match_id IN (SELECT id FROM main.matches)",
    ),
)


class AppDatabaseBuilder:
    """Build the app database from the full one."""

    def __init__(self, source: Path, target: Path) -> None:
        ...

    def build(self) -> dict[str, int]:
        """Build, check and swap in the copy; return rows per table.

        Raises AppDatabaseError listing the problems if a check fails,
        and leaves any existing target file untouched.
        """

    def _create_tables(self, connection: sqlite3.Connection) -> None:
        """Create each copied table and its indexes from the source."""
        # SELECT sql FROM src.sqlite_master
        # WHERE tbl_name IN (<the six tables>) AND sql IS NOT NULL
        # ORDER BY type = 'index'          -- tables first, then indexes

    def _copy_rows(self, connection: sqlite3.Connection) -> dict[str, int]:
        """Insert each table's rows in TABLE_COPIES order; return counts."""
        # INSERT INTO main.<table> <select>   -- once per TableCopy

    def _problems(self, connection: sqlite3.Connection) -> list[str]:
        """Return integrity and foreign-key problems; empty when sound."""
        # PRAGMA integrity_check      -- one row, 'ok', when sound
        # PRAGMA foreign_key_check    -- no rows when sound
```

```python
# scripts/build_app_db.py
"""Build data/app.db, the stats app's read-only copy of the database.

Usage: python scripts/build_app_db.py
"""
import _bootstrap  # noqa: F401

from scorecaster.config import Settings
from scorecaster.db.app_copy import AppDatabaseBuilder, AppDatabaseError


def main() -> None:
    """Build the app database and print rows per table and its size."""
    # target is data/app.db, beside the configured source database;
    # an AppDatabaseError becomes SystemExit with the listed problems


if __name__ == "__main__":
    main()
```

## Risks

- **Columns change** after a `build_features.py --rebuild` with new calculators, or a migration on a core table. Step 3 copies the source's own table definitions, so the copy follows automatically.
- **`SELECT *` copies by column position.** It's safe because step 3 creates each table with the source's own definition, so the column order is identical.
- **The API holds the file open** while it's rebuilt. Steps 1 and 6 build beside it and swap at the end. On Linux the API's open connections keep reading the old file until they reconnect.
- **Ids are copied unchanged,** so an id seen in the app (e.g. `team_id` 12 in a URL) is the same as in the full database.

## Proof

You run `python scripts/build_app_db.py`. Then:
- the printed counts match the expected column above;
- no integrity or foreign-key problems are printed (silence means both checks passed);
- the file size is printed (the spec estimated about 180 MB).

## Outcome

Built 2026-11-09, after a data refresh up to 8 Nov 2026:

| Table | Rows |
|---|---|
| competitions | 20 |
| seasons | 220 |
| matches | 73,093 |
| teams | 506 |
| team_match_features | 146,186 |
| odds | 871,103 |

- **The counts match the source** filtered by the same scope, checked with a separate read-only query.
- **No check problems were printed.**
- **No `app.db.tmp` is left behind.**
- **236 MB,** above the spec's rough 180 MB estimate. The difference is the copied indexes and the 200-column feature table.

## Expected test failures

None. No existing code changes.

## Scope ledger

**Core**

- `AppDatabaseBuilder` in `scorecaster/db/app_copy.py`: copy with `ATTACH` and `INSERT … SELECT`
- `scripts/build_app_db.py`: run the builder and print counts and size

**Optional** (ticked = written)

- [x] build into `app.db.tmp` and rename over `app.db` at the end (builder)
- [x] integrity and foreign-key checks, printed only when they find a problem (builder)
- [ ] `--source` and `--out` options (script)
- [ ] `ANALYZE` after the copy (builder)
- [ ] the `v_team_match_features` and `v_match_features` views (builder)
- [ ] timing per table in the output (script)
