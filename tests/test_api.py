"""The stats app's API, served from an app database built in the test."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from scorecaster.api.main import create_default_app
from scorecaster.db.app_copy import APP_COUNTRIES


@pytest.fixture
def app(app_db_path, monkeypatch):
    """Return the API as uvicorn builds it, reading the mini app.db."""
    source_path = app_db_path.with_name("scorecaster.db")
    monkeypatch.setenv("SCORECASTER_DB_PATH", str(source_path))
    return create_default_app()


@pytest.fixture
def client(app) -> TestClient:
    """Return a client that sends requests straight into the API."""
    return TestClient(app)


def test_competitions_come_in_menu_order(client):
    competitions = client.get("/competitions").json()
    assert len(competitions) == 20
    assert [c["code"] for c in competitions[:5]] == [
        "E0", "E1", "E2", "E3", "EC"
    ]
    countries = list(dict.fromkeys(c["country"] for c in competitions))
    assert countries == list(APP_COUNTRIES)


def test_seasons_are_listed_for_a_known_competition(client):
    assert client.get("/competitions/E0/seasons").json() == [
        {"label": "2024/25", "start_year": 2024, "end_year": 2025}
    ]


def test_an_unknown_competition_is_a_404(client):
    response = client.get("/competitions/XX/seasons")
    assert response.status_code == 404
    assert response.json() == {"detail": "No competition with code XX"}


def test_health_reports_ok(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_the_api_database_refuses_writes(app):
    with pytest.raises(OperationalError, match="readonly"):
        with app.state.database.session() as session:
            session.execute(text("DELETE FROM teams"))
