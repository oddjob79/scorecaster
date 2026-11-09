# 02 API skeleton (plan)

## Goal

A FastAPI app that reads `data/app.db` read-only and serves two endpoints:

- `GET /competitions`: the 20 competitions, England first, each country's divisions by tier.
- `GET /competitions/{code}/seasons`: one competition's seasons, newest first.

FastAPI publishes the OpenAPI schema at `/openapi.json` and interactive docs at `/docs`. Chunk 04 generates the TypeScript client from that schema.

## Depends on

01 (`data/app.db`). `fastapi` 0.162.2 and `uvicorn` 0.54.0 are already installed.

## Files that change

- `scorecaster/api/__init__.py` (new): package docstring.
- `scorecaster/api/main.py` (new): the app factory, plus a no-argument factory that uvicorn calls.
- `scorecaster/api/session.py` (new): the FastAPI dependency that hands each request a database session.
- `scorecaster/api/schemas.py` (new): Pydantic response models.
- `scorecaster/api/queries.py` (new): the database queries. Routes call these and hold no SQL, so the phase 07 MCP tools can reuse them.
- `scorecaster/api/routes/__init__.py`, `routes/competitions.py` and `routes/health.py` (new): the endpoints.
- `scorecaster/config.py`: a `Settings.app_db_path` property, `data/app.db` beside the source database.
- `scripts/build_app_db.py`: uses `Settings.app_db_path` instead of deriving the path itself.

The existing `Database` class is reused unchanged: it accepts any SQLAlchemy URL, including a read-only one.

## Order of work

1. `Settings.app_db_path`, and the build script switched to it.
2. Response models: `CompetitionResponse` and `SeasonResponse`.
3. The session dependency: it opens a session from the `Database` held on `app.state`, and closes it after the response.
4. Queries: three functions through the existing ORM models (`Competition`, `Season`).
5. Routers: the two competition endpoints (404 for an unknown code), and `/health`.
6. The app factory: create the FastAPI app, store the database on `app.state`, include both routers.
7. Run it: `uvicorn scorecaster.api.main:create_default_app --factory --reload`.

## Code outline

Signatures, docstrings and the queries; function bodies are left out.

```python
# scorecaster/api/schemas.py
"""Pydantic models for the API's JSON responses."""
from pydantic import BaseModel, ConfigDict


class CompetitionResponse(BaseModel):
    """A competition, e.g. {"code": "E0", "name": "Premier League",
    "country": "England", "tier": 1}."""

    model_config = ConfigDict(from_attributes=True)   # build from ORM rows

    code: str
    name: str
    country: str
    tier: int


class SeasonResponse(BaseModel):
    """A season, e.g. {"label": "2024/25", "start_year": 2024,
    "end_year": 2025}."""

    model_config = ConfigDict(from_attributes=True)

    label: str
    start_year: int
    end_year: int
```

```python
# scorecaster/api/session.py
"""Hand each request a session on the app database."""
from typing import Iterator

from fastapi import Request
from sqlalchemy.orm import Session


def get_session(request: Request) -> Iterator[Session]:
    """Yield a session on the app's database for one request."""
    # with request.app.state.database.session() as session: yield session
```

```python
# scorecaster/config.py, added to Settings
    @property
    def app_db_path(self) -> Path:
        """Return the stats app's database: app.db beside the source."""
        # return self.db_path.parent / "app.db"
```

```python
# scorecaster/api/queries.py
"""Read competitions and seasons from the app database."""
from sqlalchemy.orm import Session

from scorecaster.db import Competition, Season


def fetch_competitions(session: Session) -> list[Competition]:
    """Return every competition, England first, divisions by tier."""
    # select(Competition), then sorted in Python by
    # (APP_COUNTRIES.index(country), tier)  -- the app's country order


def fetch_competition_by_code(
    session: Session, code: str
) -> Competition | None:
    """Return the competition with this code, or None."""
    # select(Competition).where(Competition.code == code)


def fetch_seasons(session: Session, competition: Competition) -> list[Season]:
    """Return a competition's seasons, newest first."""
    # select(Season)
    #   .where(Season.competition_id == competition.id)
    #   .order_by(Season.start_year.desc())
```

```python
# scorecaster/api/routes/competitions.py
"""Endpoints for competitions and their seasons."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

router = APIRouter(prefix="/competitions", tags=["competitions"])


@router.get("", response_model=list[CompetitionResponse])
def list_competitions(
    session: Session = Depends(get_session),
) -> list[Competition]:
    """Return every competition in the app, in menu order."""
    # return fetch_competitions(session)


@router.get("/{code}/seasons", response_model=list[SeasonResponse])
def list_seasons(
    code: str, session: Session = Depends(get_session)
) -> list[Season]:
    """Return one competition's seasons, newest first.

    An unknown code, e.g. XX, is a 404 "No competition with code XX".
    """
    # competition = fetch_competition_by_code(session, code)
    # if competition is None: raise HTTPException(404, ...)
    # return fetch_seasons(session, competition)
```

```python
# scorecaster/api/routes/health.py
"""Report whether the API can reach its database."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

router = APIRouter(tags=["health"])


@router.get("/health")
def check_health(session: Session = Depends(get_session)) -> dict[str, str]:
    """Return {"status": "ok"} once the database answers a query."""
    # session.execute(text("SELECT 1"))  -- fails, and so 500s, if
    # app.db is missing or unreadable
```

```python
# scorecaster/api/main.py
"""Create the stats app's FastAPI application.

Run with: uvicorn scorecaster.api.main:create_default_app --factory
"""
from fastapi import FastAPI

from scorecaster.db import Database


def create_app(database: Database) -> FastAPI:
    """Return the API, reading from the given database."""
    # app = FastAPI(title="Scorecaster API")
    # app.state.database = database
    # app.include_router(competitions.router)
    # app.include_router(health.router)


def create_default_app() -> FastAPI:
    """Return the API on Settings.app_db_path, opened read-only."""
    # Database(f"sqlite:///file:{path}?mode=ro&uri=true")
    # -- SQLite refuses every write on this connection
```

`create_app` takes the database as an argument, so the phase's tests can pass a small test database. `create_default_app` exists because uvicorn's `--factory` option calls a function with no arguments.

## Risks

- **Country order lives in `APP_COUNTRIES`** in `scorecaster/db/app_copy.py`. The API imports it from there, so the copy's scope and the menu order come from one definition.
- **SQLite and threads:** FastAPI runs plain `def` endpoints in a thread pool. Each request opens its own session and connection from the engine's pool, so no connection is shared between threads.

## Proof

You run:

```bash
uvicorn scorecaster.api.main:create_default_app --factory --reload
```

Then, in a browser or with `curl`:
- `http://localhost:8000/competitions` lists 20 competitions, starting with Premier League, Championship, League One;
- `http://localhost:8000/competitions/E0/seasons` lists 11 seasons, starting 2026/27;
- `http://localhost:8000/competitions/XX/seasons` is a 404 with "No competition with code XX";
- `http://localhost:8000/health` returns `{"status": "ok"}`;
- `http://localhost:8000/docs` shows all three endpoints with their response shapes;
- `python scripts/build_app_db.py` still writes `data/app.db`.

## Outcome

Built and tested 2026-11-09:
- all five proof checks passed;
- the build script still works with `Settings.app_db_path`.

Change from the outline: `fetch_competition` is named `fetch_competition_by_code`, to say what it looks up by.

## Expected test failures

None. The `Settings` change adds a property and changes nothing existing.

## Scope ledger

**Core**

- `CompetitionResponse`, `SeasonResponse`
- `get_session` dependency
- competitions router with the two endpoints
- `create_app` and `create_default_app`

**Optional** (ticked = written)

- [x] 404 with a message for an unknown competition code (route)
- [x] `/health` endpoint for the Docker Compose health check (route)
- [x] `Settings.app_db_path`, one definition of where `app.db` lives (config + script)
- [x] queries in their own module, `scorecaster/api/queries.py` (new module)
- [ ] request logging middleware with timings (main); worth revisiting in phase 03, when slower endpoints arrive
