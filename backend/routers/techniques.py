from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session as DBSession
from typing import Optional, List
from datetime import date
import random
import models, schemas
from database import get_db
from routers.auth import get_current_user

router = APIRouter(prefix="/techniques", tags=["techniques"])


@router.get("/spotlight", response_model=schemas.TechniqueResponse)
def get_spotlight(
    current_user: models.User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    candidates = db.query(models.Technique).filter(
        models.Technique.owner_user_id == current_user.user_id,
        models.Technique.proficiency.in_(["learning", "drilling"])
    ).all()
    if not candidates:
        candidates = db.query(models.Technique).filter(
            models.Technique.owner_user_id == current_user.user_id
        ).all()
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
    db: DBSession = Depends(get_db)
):
    q = db.query(models.Technique).filter(models.Technique.owner_user_id == current_user.user_id)
    if category:
        q = q.filter(models.Technique.category == category)
    if position:
        q = q.filter(models.Technique.position.ilike(f"%{position}%"))
    if gi_nogi:
        q = q.filter(models.Technique.gi_nogi == gi_nogi)
    if proficiency:
        q = q.filter(models.Technique.proficiency == proficiency)
    if search:
        q = q.filter(models.Technique.name.ilike(f"%{search}%"))

    results = q.all()

    if tag:
        results = [t for t in results if tag in (t.tags or [])]

    # Sort
    if sort == "last_drilled":
        results.sort(key=lambda t: t.last_drilled or date.min, reverse=True)
    elif sort == "last_hit":
        results.sort(key=lambda t: t.last_hit_in_roll or date.min, reverse=True)
    else:
        results.sort(key=lambda t: t.date_added or date.min, reverse=True)

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
    t = db.query(models.Technique).filter(
        models.Technique.technique_id == technique_id,
        models.Technique.owner_user_id == current_user.user_id,
    ).first()
    if not t:
        raise HTTPException(status_code=404, detail="Technique not found")
    return t


@router.put("/{technique_id}", response_model=schemas.TechniqueResponse)
def update_technique(
    technique_id: str,
    data: schemas.TechniqueUpdate,
    current_user: models.User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    t = db.query(models.Technique).filter(
        models.Technique.technique_id == technique_id,
        models.Technique.owner_user_id == current_user.user_id,
    ).first()
    if not t:
        raise HTTPException(status_code=404, detail="Technique not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(t, k, v)
    db.commit()
    db.refresh(t)
    return t


@router.delete("/{technique_id}", status_code=204)
def delete_technique(
    technique_id: str,
    current_user: models.User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    t = db.query(models.Technique).filter(
        models.Technique.technique_id == technique_id,
        models.Technique.owner_user_id == current_user.user_id,
    ).first()
    if not t:
        raise HTTPException(status_code=404, detail="Technique not found")
    db.delete(t)
    db.commit()


@router.post("/{technique_id}/link", status_code=201)
def link_techniques(
    technique_id: str,
    data: schemas.LinkRequest,
    current_user: models.User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    source = db.query(models.Technique).filter(
        models.Technique.technique_id == technique_id,
        models.Technique.owner_user_id == current_user.user_id,
    ).first()
    target = db.query(models.Technique).filter(
        models.Technique.technique_id == data.to_technique_id,
        models.Technique.owner_user_id == current_user.user_id,
    ).first()
    if not source or not target:
        raise HTTPException(status_code=404, detail="Technique not found")
    link = models.LinkedTechnique(
        from_technique_id=technique_id,
        to_technique_id=data.to_technique_id,
        relationship_type=data.relationship_type
    )
    db.add(link)
    db.commit()
    return {"status": "linked"}


@router.delete("/{technique_id}/link/{to_id}", status_code=204)
def unlink_techniques(
    technique_id: str,
    to_id: str,
    current_user: models.User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    source = db.query(models.Technique).filter(
        models.Technique.technique_id == technique_id,
        models.Technique.owner_user_id == current_user.user_id,
    ).first()
    target = db.query(models.Technique).filter(
        models.Technique.technique_id == to_id,
        models.Technique.owner_user_id == current_user.user_id,
    ).first()
    if not source or not target:
        raise HTTPException(status_code=404, detail="Technique not found")
    link = db.query(models.LinkedTechnique).filter(
        models.LinkedTechnique.from_technique_id == technique_id,
        models.LinkedTechnique.to_technique_id == to_id
    ).first()
    if link:
        db.delete(link)
        db.commit()
