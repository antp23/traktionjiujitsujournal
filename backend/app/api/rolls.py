"""Roll (sparring round) log."""
from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session as DBSession

from app import models, schemas
from app.api.deps import apply_partial_update, get_current_user, get_owned_or_404
from app.db import get_db
from app.services import stats

router = APIRouter(prefix="/rolls", tags=["rolls"])


def _owned_roll(db: DBSession, roll_id: str, user: models.User) -> models.RollLog:
    return get_owned_or_404(
        db, models.RollLog, models.RollLog.roll_id, roll_id,
        user.user_id, "Roll not found",
    )


@router.get("/stats/summary")
def roll_stats(
    current_user: models.User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    return stats.roll_stats_for_owner(db, current_user.user_id)


@router.get("", response_model=List[schemas.RollLogResponse])
def list_rolls(
    session_id: Optional[str] = None,
    partner: Optional[str] = None,
    current_user: models.User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    query = db.query(models.RollLog).filter(
        models.RollLog.owner_user_id == current_user.user_id
    )
    if session_id:
        query = query.filter(models.RollLog.session_id == session_id)
    if partner:
        query = query.filter(models.RollLog.partner.ilike(f"%{partner}%"))
    return query.all()


@router.post("", response_model=schemas.RollLogResponse, status_code=201)
def create_roll(
    data: schemas.RollLogCreate,
    current_user: models.User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    # A roll can only be attached to a session the caller owns.
    get_owned_or_404(
        db, models.Session, models.Session.session_id, data.session_id,
        current_user.user_id, "Session not found",
    )
    roll = models.RollLog(owner_user_id=current_user.user_id, **data.model_dump())
    db.add(roll)
    db.commit()
    db.refresh(roll)
    return roll


@router.get("/{roll_id}", response_model=schemas.RollLogResponse)
def get_roll(
    roll_id: str,
    current_user: models.User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    return _owned_roll(db, roll_id, current_user)


@router.put("/{roll_id}", response_model=schemas.RollLogResponse)
def update_roll(
    roll_id: str,
    data: schemas.RollLogUpdate,
    current_user: models.User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    roll = _owned_roll(db, roll_id, current_user)
    apply_partial_update(roll, data)
    db.commit()
    db.refresh(roll)
    return roll


@router.delete("/{roll_id}", status_code=204)
def delete_roll(
    roll_id: str,
    current_user: models.User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    roll = _owned_roll(db, roll_id, current_user)
    db.delete(roll)
    db.commit()
