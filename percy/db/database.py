"""Database engine and schema management."""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from sqlalchemy import Engine, create_engine, event, inspect
from sqlalchemy.orm import Session, sessionmaker

from percy.db.models import Base


class Database:
    """Owns the SQLAlchemy engine and hands out sessions."""

    def __init__(self, url: str) -> None:
        self.url = url
        self.engine: Engine = create_engine(url, future=True)
        event.listen(self.engine, "connect", self._enable_foreign_keys)
        self._sessions = sessionmaker(self.engine, expire_on_commit=False)

    @classmethod
    def for_path(cls, path: Path) -> "Database":
        """Create a Database for a SQLite file, creating parent directories."""
        path.parent.mkdir(parents=True, exist_ok=True)
        return cls(f"sqlite:///{path}")

    @staticmethod
    def _enable_foreign_keys(dbapi_conn, _record) -> None:
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    def existing_tables(self) -> set[str]:
        """Names of tables already present in the database."""
        return set(inspect(self.engine).get_table_names())

    def create_schema(self) -> list[str]:
        """Create any missing raw tables; never drops or alters existing ones. Returns created names."""
        before = self.existing_tables()
        Base.metadata.create_all(self.engine, checkfirst=True)
        return sorted(self.existing_tables() - before)

    @contextmanager
    def session(self) -> Iterator[Session]:
        """Transactional session scope: commits on success, rolls back on error."""
        session = self._sessions()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
