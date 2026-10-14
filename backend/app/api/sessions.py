"""Training session log."""
from datetime import date, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session as DBSession

from app import models, schemas
from app.api.deps import apply_partial_update, get_current_user, get_owned_or_404
from app.db import get_db
from app.services import stats

router = APIRouter(prefix="/sessions", tags=["sessions"])


def _owned_session(db: DBSession, session_id: str, user: models.User) -> models.Session:
    return get_owned_or_404(
        db, models.Session, models.Session.session_id, session_id,
        user.user_id, "Session not found",
    )


@router.get("", response_model=List[schemas.SessionResponse])
def list_sessions(
    session_type: Optional[str] = None,
    gym_location: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    limit: int = Query(100, ge=1, le=500),
    current_user: models.User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    query = db.query(models.Session).filter(
        models.Session.owner_user_id == current_user.user_id
    )
    if session_type:
        query = query.filter(models.Session.session_type == session_type)
    if gym_location:
        query = query.filter(models.Session.gym_location == gym_location)
    if date_from:
        query = query.filter(models.Session.date >= date_from)
    if date_to:
        query = query.filter(models.Session.date <= date_to)
    return query.order_by(models.Session.date.desc()).limit(limit).all()


@router.post("", response_model=schemas.SessionResponse, status_code=201)
def create_session(
    data: schemas.SessionCreate,
    current_user: models.User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    session = models.Session(owner_user_id=current_user.user_id, **data.model_dump())
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("/stats/summary")
def session_stats(
    current_user: models.User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    return stats.session_stats_for_owner(db, current_user.user_id)


ROAD_START = date(2026, 10, 12)
ROAD_GOAL_DATE = date(2027, 4, 25)
ROAD_TOTAL_HOURS = 150.0
ROAD_MILESTONES = [(75.0, "4th stripe"), (150.0, "Brown belt test")]


@router.get("/stats/road-to-brown")
def road_to_brown(
    today: Optional[date] = None,
    current_user: models.User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """Hours logged since the 3rd stripe toward the 150h brown belt test."""
    today = today or date.today()
    rows = db.query(models.Session.date, models.Session.duration_minutes).filter(
        models.Session.owner_user_id == current_user.user_id,
        models.Session.attended.is_(True),
        models.Session.date >= ROAD_START,
        models.Session.date <= today,
    ).all()
    hours = round(sum((m or 0) for _, m in rows) / 60.0, 2)
    window_start = today - timedelta(days=27)
    recent = sum((m or 0) for d, m in rows if d >= window_start) / 60.0
    next_ms = next(({"hours": h, "label": l} for h, l in ROAD_MILESTONES if hours < h), None)
    weeks_left = max((ROAD_GOAL_DATE - today).days, 0) / 7.0
    remaining_total = max(ROAD_TOTAL_HOURS - hours, 0.0)
    if remaining_total == 0:
        needed = 0.0
    elif weeks_left > 0:
        needed = round(remaining_total / weeks_left, 2)
    else:
        needed = None
    return {
        "start_date": ROAD_START.isoformat(),
        "goal_date": ROAD_GOAL_DATE.isoformat(),
        "total_hours": ROAD_TOTAL_HOURS,
        "hours_logged": hours,
        "milestones": [{"hours": h, "label": l, "reached": hours >= h} for h, l in ROAD_MILESTONES],
        "next_milestone": next_ms,
        "hours_to_next_milestone": round(next_ms["hours"] - hours, 2) if next_ms else 0.0,
        "hours_remaining": round(remaining_total, 2),
        "weeks_until_goal": round(weeks_left, 1),
        "weekly_pace_needed": needed,
        "four_week_avg_pace": round(recent / 4.0, 2),
    }


@router.get("/{session_id}", response_model=schemas.SessionResponse)
def get_session(
    session_id: str,
    current_user: models.User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    return _owned_session(db, session_id, current_user)


@router.put("/{session_id}", response_model=schemas.SessionResponse)
def update_session(
    session_id: str,
    data: schemas.SessionUpdate,
    current_user: models.User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    session = _owned_session(db, session_id, current_user)
    apply_partial_update(session, data)
    db.commit()
    db.refresh(session)
    return session


@router.delete("/{session_id}", status_code=204)
def delete_session(
    session_id: str,
    current_user: models.User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    session = _owned_session(db, session_id, current_user)
    db.delete(session)
    db.commit()
