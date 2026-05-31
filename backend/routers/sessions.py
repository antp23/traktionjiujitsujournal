from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import func
from typing import Optional, List
from datetime import date, timedelta
import models, schemas
from database import get_db
from routers.auth import get_current_user

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("", response_model=List[schemas.SessionResponse])
def list_sessions(
    session_type: Optional[str] = None,
    gym_location: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    limit: int = Query(100, ge=1, le=500),
    current_user: models.User = Depends(get_current_user),
    db: DBSession = Depends(get_db)
):
    q = db.query(models.Session).filter(models.Session.owner_user_id == current_user.user_id)
    if session_type:
        q = q.filter(models.Session.session_type == session_type)
    if gym_location:
        q = q.filter(models.Session.gym_location == gym_location)
    if date_from:
        q = q.filter(models.Session.date >= date_from)
    if date_to:
        q = q.filter(models.Session.date <= date_to)
    return q.order_by(models.Session.date.desc()).limit(limit).all()


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
    return _session_stats_for_owner(db, current_user.user_id)


def _session_stats_for_owner(db: DBSession, owner_user_id: str):
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)

    all_sessions = db.query(models.Session).filter(
        models.Session.owner_user_id == owner_user_id,
        models.Session.attended == True,
    ).all()
    total_sessions = len(all_sessions)
    total_minutes = sum(s.duration_minutes or 0 for s in all_sessions)

    sessions_this_week = db.query(models.Session).filter(
        models.Session.owner_user_id == owner_user_id,
        models.Session.attended == True,
        models.Session.date >= week_start
    ).count()

    sessions_this_month = db.query(models.Session).filter(
        models.Session.owner_user_id == owner_user_id,
        models.Session.attended == True,
        models.Session.date >= month_start
    ).count()

    # Streak: consecutive calendar weeks (Mon–Sun) with at least one session
    attended_dates = set(
        s.date for s in db.query(models.Session).filter(
            models.Session.owner_user_id == owner_user_id,
            models.Session.attended == True,
        ).all()
    )
    def week_start_for(d):
        return d - timedelta(days=d.weekday())

    streak = 0
    check_week = week_start_for(today)
    while True:
        week_end = check_week + timedelta(days=6)
        if any(check_week <= d <= week_end for d in attended_dates):
            streak += 1
            check_week -= timedelta(weeks=1)
        else:
            break

    # Last 30/90 day attendance rate (sessions per week)
    last_30 = db.query(models.Session).filter(
        models.Session.owner_user_id == owner_user_id,
        models.Session.attended == True,
        models.Session.date >= today - timedelta(days=30)
    ).count()
    last_90 = db.query(models.Session).filter(
        models.Session.owner_user_id == owner_user_id,
        models.Session.attended == True,
        models.Session.date >= today - timedelta(days=90)
    ).count()

    return {
        "total_sessions": total_sessions,
        "total_minutes": total_minutes,
        "sessions_this_week": sessions_this_week,
        "sessions_this_month": sessions_this_month,
        "current_streak": streak,
        "last_30_day_count": last_30,
        "last_90_day_count": last_90,
        "last_30_day_rate": round(last_30 / 30 * 7, 1),  # avg sessions/week
        "last_90_day_rate": round(last_90 / 90 * 7, 1),
    }


@router.get("/{session_id}", response_model=schemas.SessionResponse)
def get_session(
    session_id: str,
    current_user: models.User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    session = db.query(models.Session).filter(
        models.Session.session_id == session_id,
        models.Session.owner_user_id == current_user.user_id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.put("/{session_id}", response_model=schemas.SessionResponse)
def update_session(
    session_id: str,
    data: schemas.SessionUpdate,
    current_user: models.User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    session = db.query(models.Session).filter(
        models.Session.session_id == session_id,
        models.Session.owner_user_id == current_user.user_id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(session, k, v)
    db.commit()
    db.refresh(session)
    return session


@router.delete("/{session_id}", status_code=204)
def delete_session(
    session_id: str,
    current_user: models.User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    session = db.query(models.Session).filter(
        models.Session.session_id == session_id,
        models.Session.owner_user_id == current_user.user_id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    db.delete(session)
    db.commit()
