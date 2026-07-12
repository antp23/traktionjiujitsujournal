"""Training session log."""
from datetime import date
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
