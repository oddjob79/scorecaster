"""Report whether the API can reach its database."""
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from scorecaster.api.session import get_session

router = APIRouter(tags=["health"])


@router.get("/health")
def check_health(session: Session = Depends(get_session)) -> dict[str, str]:
    """Return {"status": "ok"} once the database answers a query.

    A missing or unreadable app.db makes the query fail, so the endpoint
    answers 500 instead.
    """
    session.execute(text("SELECT 1"))
    return {"status": "ok"}
