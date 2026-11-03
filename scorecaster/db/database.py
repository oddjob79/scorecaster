"""Database engine and schema management."""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Iterable, Iterator

from sqlalchemy import Engine, create_engine, event, inspect
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session, sessionmaker

from scorecaster.db.models import Base, Competition

if TYPE_CHECKING:
    from scorecaster.config import LeagueConfig


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

    def upsert_competitions(self, leagues: Iterable[LeagueConfig]) -> int:
        """Insert or update one competitions row per league, keyed by code. Returns the number of leagues."""
        rows = [league.model_dump(include={"code", "country", "name", "tier"})
                for league in leagues]
        stmt = sqlite_insert(Competition).values(rows)
        stmt = stmt.on_conflict_do_update(
            index_elements=["code"],
            set_={col: stmt.excluded[col] for col in ("country", "name", "tier")},
        )
        with self.engine.begin() as conn:
            conn.execute(stmt)
        return len(rows)

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
