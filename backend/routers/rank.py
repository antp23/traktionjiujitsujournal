from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession
from typing import List
import models, schemas
from database import get_db
from routers.auth import get_current_user

router = APIRouter(prefix="/rank", tags=["rank"])


@router.get("", response_model=List[schemas.RankLogResponse])
def list_rank(
    current_user: models.User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    return db.query(models.RankLog).filter(
        models.RankLog.owner_user_id == current_user.user_id
    ).order_by(models.RankLog.date_awarded.desc()).all()


@router.get("/current", response_model=schemas.RankLogResponse)
def current_rank(
    current_user: models.User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    rank = db.query(models.RankLog).filter(
        models.RankLog.owner_user_id == current_user.user_id
    ).order_by(models.RankLog.date_awarded.desc()).first()
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
    rank = db.query(models.RankLog).filter(
        models.RankLog.rank_id == rank_id,
        models.RankLog.owner_user_id == current_user.user_id,
    ).first()
    if not rank:
        raise HTTPException(status_code=404, detail="Rank entry not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(rank, k, v)
    db.commit()
    db.refresh(rank)
    return rank


@router.delete("/{rank_id}", status_code=204)
def delete_rank(
    rank_id: str,
    current_user: models.User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    rank = db.query(models.RankLog).filter(
        models.RankLog.rank_id == rank_id,
        models.RankLog.owner_user_id == current_user.user_id,
    ).first()
    if not rank:
        raise HTTPException(status_code=404, detail="Rank entry not found")
    db.delete(rank)
    db.commit()
