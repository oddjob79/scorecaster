"""Read competitions and seasons from the app database."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from scorecaster.db import Competition, Season
from scorecaster.db.app_copy import APP_COUNTRIES


def fetch_competitions(session: Session) -> list[Competition]:
    """Return every competition, England first, divisions by tier."""
    competitions = session.scalars(select(Competition)).all()
    return sorted(competitions, key=_menu_order)


def fetch_competition_by_code(
    session: Session, code: str
) -> Competition | None:
    """Return the competition with this code, or None."""
    return session.scalars(
        select(Competition).where(Competition.code == code)
    ).one_or_none()


def fetch_seasons(
    session: Session, competition: Competition
) -> list[Season]:
    """Return a competition's seasons, newest first."""
    return list(
        session.scalars(
            select(Season)
            .where(Season.competition_id == competition.id)
            .order_by(Season.start_year.desc())
        )
    )


def _menu_order(competition: Competition) -> tuple[int, int]:
    """Sort key: the app's country order, then tier within a country."""
    return APP_COUNTRIES.index(competition.country), competition.tier
