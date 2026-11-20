"""Hand each request a session on the app database."""
from __future__ import annotations

from typing import Iterator

from fastapi import Request
from sqlalchemy.orm import Session


def get_session(request: Request) -> Iterator[Session]:
    """Yield a session on the app's database for one request."""
    with request.app.state.database.session() as session:
        yield session
