"""Belt/stripe promotion history."""
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession

from app import models, schemas
from app.api.deps import apply_partial_update, get_current_user, get_owned_or_404
from app.db import get_db

router = APIRouter(prefix="/rank", tags=["rank"])


def _owned_rank(db: DBSession, rank_id: str, user: models.User) -> models.RankLog:
    return get_owned_or_404(
        db, models.RankLog, models.RankLog.rank_id, rank_id,
        user.user_id, "Rank entry not found",
    )


@router.get("", response_model=List[schemas.RankLogResponse])
def list_rank(
    current_user: models.User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    return (
        db.query(models.RankLog)
        .filter(models.RankLog.owner_user_id == current_user.user_id)
        .order_by(models.RankLog.date_awarded.desc())
        .all()
    )


@router.get("/current", response_model=schemas.RankLogResponse)
def current_rank(
    current_user: models.User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    rank = (
        db.query(models.RankLog)
        .filter(models.RankLog.owner_user_id == current_user.user_id)
        .order_by(models.RankLog.date_awarded.desc())
        .first()
    )
    if not rank:
        raise HTTPException(status_code=404, detail="No rank entries found")
    return rank


@router.post("", response_model=schemas.RankLogResponse, status_code=201)
def add_rank(
    data: schemas.RankLogCreate,
    current_user: models.User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    rank = models.RankLog(owner_user_id=current_user.user_id, **data.model_dump())
    db.add(rank)
    db.commit()
    db.refresh(rank)
    return rank


@router.put("/{rank_id}", response_model=schemas.RankLogResponse)
def update_rank(
    rank_id: str,
    data: schemas.RankLogUpdate,
    current_user: models.User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    rank = _owned_rank(db, rank_id, current_user)
    apply_partial_update(rank, data)
    db.commit()
    db.refresh(rank)
    return rank


@router.delete("/{rank_id}", status_code=204)
def delete_rank(
    rank_id: str,
    current_user: models.User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    rank = _owned_rank(db, rank_id, current_user)
    db.delete(rank)
    db.commit()
