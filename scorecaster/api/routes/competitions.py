"""Endpoints for competitions and their seasons."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from scorecaster.api.queries import (
    fetch_competition_by_code,
    fetch_competitions,
    fetch_seasons,
)
from scorecaster.api.schemas import CompetitionResponse, SeasonResponse
from scorecaster.api.session import get_session
from scorecaster.db import Competition, Season

router = APIRouter(prefix="/competitions", tags=["competitions"])


@router.get("", response_model=list[CompetitionResponse])
def list_competitions(
    session: Session = Depends(get_session),
) -> list[Competition]:
    """Return every competition in the app, in menu order."""
    return fetch_competitions(session)


@router.get("/{code}/seasons", response_model=list[SeasonResponse])
def list_seasons(
    code: str, session: Session = Depends(get_session)
) -> list[Season]:
    """Return one competition's seasons, newest first.

    An unknown code, e.g. XX, is a 404 "No competition with code XX".
    """
    competition = fetch_competition_by_code(session, code)
    if competition is None:
        raise HTTPException(404, f"No competition with code {code}")
    return fetch_seasons(session, competition)
