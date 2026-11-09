"""Create the stats app's FastAPI application.

Run with: uvicorn scorecaster.api.main:create_default_app --factory
"""
from fastapi import FastAPI

from scorecaster.api.routes import competitions, health
from scorecaster.config import Settings
from scorecaster.db import Database


def create_app(database: Database) -> FastAPI:
    """Return the API, reading from the given database."""
    app = FastAPI(title="Scorecaster API")
    app.state.database = database
    app.include_router(competitions.router)
    app.include_router(health.router)
    return app


def create_default_app() -> FastAPI:
    """Return the API on Settings.app_db_path, opened read-only."""
    path = Settings.from_env().app_db_path
    # mode=ro makes SQLite refuse every write on this connection.
    database = Database(f"sqlite:///file:{path}?mode=ro&uri=true")
    return create_app(database)
