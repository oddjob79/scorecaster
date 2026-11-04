"""Insert rows, or update them where they already exist (SQLite)."""
from __future__ import annotations

from sqlalchemy import Table
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session


def upsert(
    session: Session, table: Table, rows: list[dict], key: list[str]
) -> None:
    """Insert rows, updating non-key columns where the key already exists.

    `key` must match a unique constraint on the table, e.g. the odds
    table's (match, bookmaker, market, selection, line, timing).
    """
    if not rows:
        return
    statement = sqlite_insert(table)
    updates = {
        column: statement.excluded[column]
        for column in rows[0]
        if column not in key
    }
    statement = statement.on_conflict_do_update(
        index_elements=key, set_=updates
    )
    session.connection().execute(statement, rows)
