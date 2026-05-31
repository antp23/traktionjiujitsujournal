from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session as DBSession
from typing import Optional, List
from collections import Counter
import models, schemas
from database import get_db
from routers.auth import get_current_user

router = APIRouter(prefix="/rolls", tags=["rolls"])


@router.get("/stats/summary")
def roll_stats(
    current_user: models.User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    return _roll_stats_for_owner(db, current_user.user_id)


def _roll_stats_for_owner(db: DBSession, owner_user_id: str):
    rolls = db.query(models.RollLog).filter(models.RollLog.owner_user_id == owner_user_id).all()
    if not rolls:
        return {"total_rolls": 0}

    total = len(rolls)
    outcomes = Counter(r.outcome for r in rolls)
    wins = outcomes.get("submission_win", 0) + outcomes.get("points_win", 0)
    losses = outcomes.get("submission_loss", 0) + outcomes.get("points_loss", 0)
    draws = outcomes.get("draw", 0)

    subs_scored = [r.submission_scored for r in rolls if r.submission_scored]
    subs_received = [r.submission_received for r in rolls if r.submission_received]

    positions_held = []
    positions_given = []
    for r in rolls:
        positions_held.extend(r.dominant_positions_held or [])
        positions_given.extend(r.dominant_positions_given or [])

    partner_stats = {}
    for r in rolls:
        p = r.partner
        if p not in partner_stats:
            partner_stats[p] = {"wins": 0, "losses": 0, "draws": 0, "total": 0}
        partner_stats[p]["total"] += 1
        if r.outcome in ("submission_win", "points_win"):
            partner_stats[p]["wins"] += 1
        elif r.outcome in ("submission_loss", "points_loss"):
            partner_stats[p]["losses"] += 1
        else:
            partner_stats[p]["draws"] += 1

    return {
        "total_rolls": total,
        "wins": wins,
        "losses": losses,
        "draws": draws,
        "win_rate": round(wins / total * 100, 1) if total else 0,
        "top_submissions_scored": Counter(subs_scored).most_common(5),
        "top_submissions_received": Counter(subs_received).most_common(5),
        "top_positions_held": Counter(positions_held).most_common(5),
        "top_positions_given": Counter(positions_given).most_common(5),
        "partner_breakdown": partner_stats,
    }


@router.get("", response_model=List[schemas.RollLogResponse])
def list_rolls(
    session_id: Optional[str] = None,
    partner: Optional[str] = None,
    current_user: models.User = Depends(get_current_user),
    db: DBSession = Depends(get_db)
):
    q = db.query(models.RollLog).filter(models.RollLog.owner_user_id == current_user.user_id)
    if session_id:
        q = q.filter(models.RollLog.session_id == session_id)
    if partner:
        q = q.filter(models.RollLog.partner.ilike(f"%{partner}%"))
    return q.all()


@router.post("", response_model=schemas.RollLogResponse, status_code=201)
def create_roll(
    data: schemas.RollLogCreate,
    current_user: models.User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    session = db.query(models.Session).filter(
        models.Session.session_id == data.session_id,
        models.Session.owner_user_id == current_user.user_id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
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
    roll = db.query(models.RollLog).filter(
        models.RollLog.roll_id == roll_id,
        models.RollLog.owner_user_id == current_user.user_id,
    ).first()
    if not roll:
        raise HTTPException(status_code=404, detail="Roll not found")
    return roll


@router.put("/{roll_id}", response_model=schemas.RollLogResponse)
def update_roll(
    roll_id: str,
    data: schemas.RollLogUpdate,
    current_user: models.User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    roll = db.query(models.RollLog).filter(
        models.RollLog.roll_id == roll_id,
        models.RollLog.owner_user_id == current_user.user_id,
    ).first()
    if not roll:
        raise HTTPException(status_code=404, detail="Roll not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(roll, k, v)
    db.commit()
    db.refresh(roll)
    return roll


@router.delete("/{roll_id}", status_code=204)
def delete_roll(
    roll_id: str,
    current_user: models.User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    roll = db.query(models.RollLog).filter(
        models.RollLog.roll_id == roll_id,
        models.RollLog.owner_user_id == current_user.user_id,
    ).first()
    if not roll:
        raise HTTPException(status_code=404, detail="Roll not found")
    db.delete(roll)
    db.commit()
