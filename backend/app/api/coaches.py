"""Coach directory.

v1 quirk kept deliberately: this resource has no user auth and no ownership —
it is a small shared directory of coach names. See the development plan's
"preserved quirks" table before changing this contract.
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession

from app import models, schemas
from app.db import get_db

router = APIRouter(prefix="/coaches", tags=["coaches"])


def _coach_or_404(db: DBSession, coach_id: str) -> models.Coach:
    coach = db.query(models.Coach).filter(models.Coach.coach_id == coach_id).first()
    if not coach:
        raise HTTPException(status_code=404, detail="Coach not found")
    return coach


@router.get("", response_model=List[schemas.CoachResponse])
def list_coaches(db: DBSession = Depends(get_db)):
    return db.query(models.Coach).all()


@router.post("", response_model=schemas.CoachResponse, status_code=201)
def create_coach(data: schemas.CoachCreate, db: DBSession = Depends(get_db)):
    coach = models.Coach(**data.model_dump())
    db.add(coach)
    db.commit()
    db.refresh(coach)
    return coach


@router.get("/{coach_id}", response_model=schemas.CoachResponse)
def get_coach(coach_id: str, db: DBSession = Depends(get_db)):
    return _coach_or_404(db, coach_id)


@router.put("/{coach_id}", response_model=schemas.CoachResponse)
def update_coach(coach_id: str, data: schemas.CoachUpdate, db: DBSession = Depends(get_db)):
    coach = _coach_or_404(db, coach_id)
    # v1 quirk: exclude_none (a field cannot be nulled through this endpoint).
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(coach, field, value)
    db.commit()
    db.refresh(coach)
    return coach


@router.delete("/{coach_id}", status_code=204)
def delete_coach(coach_id: str, db: DBSession = Depends(get_db)):
    coach = _coach_or_404(db, coach_id)
    db.delete(coach)
    db.commit()
