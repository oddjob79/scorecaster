"""Own the database engine, the schema and transactional sessions."""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from sqlalchemy import Engine, create_engine, event, inspect
from sqlalchemy.orm import Session, sessionmaker

from scorecaster.db.models import Base


class Database:
    """Hold the SQLAlchemy engine and hand out sessions.

    Every connection has SQLite's foreign-key checks switched on, which
    SQLite leaves off by default.
    """

    def __init__(self, url: str) -> None:
        self.url = url
        self.engine: Engine = create_engine(url, future=True)
        event.listen(self.engine, "connect", _enable_foreign_keys)
        self._sessions = sessionmaker(self.engine, expire_on_commit=False)

    @classmethod
    def for_path(cls, path: Path) -> Database:
        """Open a SQLite file, creating its folder if needed."""
        path.parent.mkdir(parents=True, exist_ok=True)
        return cls(f"sqlite:///{path}")

    def existing_tables(self) -> set[str]:
        """Return the names of the tables already in the database."""
        return set(inspect(self.engine).get_table_names())

    def create_schema(self) -> list[str]:
        """Create any missing tables and return their names.

        Existing tables are never dropped or altered.
        """
        before = self.existing_tables()
        Base.metadata.create_all(self.engine, checkfirst=True)
        return sorted(self.existing_tables() - before)

    def schema_differences(self) -> list[str]:
        """Describe every column the models and the stored tables disagree on.

        `create_schema` only adds missing tables, never columns, so a
        column added to a model later is silently absent from an existing
        database. An empty list means the two match.
        """
        inspector = inspect(self.engine)
        stored_tables = set(inspector.get_table_names())
        differences = []
        for table in Base.metadata.sorted_tables:
            if table.name not in stored_tables:
                continue
            stored = {c["name"] for c in inspector.get_columns(table.name)}
            modelled = {column.name for column in table.columns}
            for name in sorted(modelled - stored):
                differences.append(f"{table.name}.{name}: not in database")
            for name in sorted(stored - modelled):
                differences.append(f"{table.name}.{name}: not in models")
        return differences

    @contextmanager
    def session(self) -> Iterator[Session]:
        """Yield a session that commits on success and rolls back on error."""
        session = self._sessions()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


def _enable_foreign_keys(dbapi_connection, _connection_record) -> None:
    """Switch on SQLite's foreign-key checks for a new connection."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
