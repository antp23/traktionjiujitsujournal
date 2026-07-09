"""Technique library."""
import random
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession

from app import models, schemas
from app.api.deps import apply_partial_update, get_current_user, get_owned_or_404
from app.db import get_db

router = APIRouter(prefix="/techniques", tags=["techniques"])


def _owned_technique(db: DBSession, technique_id: str, user: models.User) -> models.Technique:
    return get_owned_or_404(
        db, models.Technique, models.Technique.technique_id, technique_id,
        user.user_id, "Technique not found",
    )


@router.get("/spotlight", response_model=schemas.TechniqueResponse)
def get_spotlight(
    current_user: models.User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """A technique to review today — prefers ones still being learned/drilled."""
    base = db.query(models.Technique).filter(
        models.Technique.owner_user_id == current_user.user_id
    )
    candidates = base.filter(models.Technique.proficiency.in_(["learning", "drilling"])).all()
    if not candidates:
        candidates = base.all()
    if not candidates:
        raise HTTPException(status_code=404, detail="No techniques found")
    return random.choice(candidates)


@router.get("", response_model=List[schemas.TechniqueResponse])
def list_techniques(
    category: Optional[str] = None,
    position: Optional[str] = None,
    gi_nogi: Optional[str] = None,
    proficiency: Optional[str] = None,
    tag: Optional[str] = None,
    search: Optional[str] = None,
    sort: Optional[str] = "date_added",
    current_user: models.User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    query = db.query(models.Technique).filter(
        models.Technique.owner_user_id == current_user.user_id
    )
    if category:
        query = query.filter(models.Technique.category == category)
    if position:
        query = query.filter(models.Technique.position.ilike(f"%{position}%"))
    if gi_nogi:
        query = query.filter(models.Technique.gi_nogi == gi_nogi)
    if proficiency:
        query = query.filter(models.Technique.proficiency == proficiency)
    if search:
        query = query.filter(models.Technique.name.ilike(f"%{search}%"))

    results = query.all()
    if tag:
        results = [t for t in results if tag in (t.tags or [])]

    sort_keys = {
        "last_drilled": lambda t: t.last_drilled or date.min,
        "last_hit": lambda t: t.last_hit_in_roll or date.min,
    }
    key = sort_keys.get(sort, lambda t: t.date_added or date.min)
    results.sort(key=key, reverse=True)
    return results


@router.post("", response_model=schemas.TechniqueResponse, status_code=201)
def create_technique(
    data: schemas.TechniqueCreate,
    current_user: models.User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    technique = models.Technique(owner_user_id=current_user.user_id, **data.model_dump())
    db.add(technique)
    db.commit()
    db.refresh(technique)
    return technique


@router.get("/{technique_id}", response_model=schemas.TechniqueResponse)
def get_technique(
    technique_id: str,
    current_user: models.User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    return _owned_technique(db, technique_id, current_user)


@router.put("/{technique_id}", response_model=schemas.TechniqueResponse)
def update_technique(
    technique_id: str,
    data: schemas.TechniqueUpdate,
    current_user: models.User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    technique = _owned_technique(db, technique_id, current_user)
    apply_partial_update(technique, data)
    db.commit()
    db.refresh(technique)
    return technique


@router.delete("/{technique_id}", status_code=204)
def delete_technique(
    technique_id: str,
    current_user: models.User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    technique = _owned_technique(db, technique_id, current_user)
    db.delete(technique)
    db.commit()


@router.post("/{technique_id}/link", status_code=201)
def link_techniques(
    technique_id: str,
    data: schemas.LinkRequest,
    current_user: models.User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    _owned_technique(db, technique_id, current_user)
    _owned_technique(db, data.to_technique_id, current_user)
    db.add(models.LinkedTechnique(
        from_technique_id=technique_id,
        to_technique_id=data.to_technique_id,
        relationship_type=data.relationship_type,
    ))
    db.commit()
    return {"status": "linked"}


@router.delete("/{technique_id}/link/{to_id}", status_code=204)
def unlink_techniques(
    technique_id: str,
    to_id: str,
    current_user: models.User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    _owned_technique(db, technique_id, current_user)
    _owned_technique(db, to_id, current_user)
    link = (
        db.query(models.LinkedTechnique)
        .filter(
            models.LinkedTechnique.from_technique_id == technique_id,
            models.LinkedTechnique.to_technique_id == to_id,
        )
        .first()
    )
    if link:
        db.delete(link)
        db.commit()
