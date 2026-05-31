from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session as DBSession
from typing import Optional, List
from datetime import datetime
import models, schemas
from database import get_db
from routers.auth import get_current_user

router = APIRouter(prefix="/notes", tags=["notes"])


@router.get("", response_model=List[schemas.NoteResponse])
def list_notes(
    search: Optional[str] = None,
    tag: Optional[str] = None,
    current_user: models.User = Depends(get_current_user),
    db: DBSession = Depends(get_db)
):
    q = db.query(models.Note).filter(models.Note.owner_user_id == current_user.user_id)
    if search:
        q = q.filter(
            models.Note.content.ilike(f"%{search}%") |
            models.Note.title.ilike(f"%{search}%")
        )
    results = q.order_by(models.Note.created_at.desc()).all()
    if tag:
        results = [n for n in results if tag in (n.tags or [])]
    return results


@router.post("", response_model=schemas.NoteResponse, status_code=201)
def create_note(
    data: schemas.NoteCreate,
    current_user: models.User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    note = models.Note(owner_user_id=current_user.user_id, **data.model_dump())
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


@router.get("/{note_id}", response_model=schemas.NoteResponse)
def get_note(
    note_id: str,
    current_user: models.User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    note = db.query(models.Note).filter(
        models.Note.note_id == note_id,
        models.Note.owner_user_id == current_user.user_id,
    ).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@router.put("/{note_id}", response_model=schemas.NoteResponse)
def update_note(
    note_id: str,
    data: schemas.NoteUpdate,
    current_user: models.User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    note = db.query(models.Note).filter(
        models.Note.note_id == note_id,
        models.Note.owner_user_id == current_user.user_id,
    ).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(note, k, v)
    note.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(note)
    return note


@router.delete("/{note_id}", status_code=204)
def delete_note(
    note_id: str,
    current_user: models.User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    note = db.query(models.Note).filter(
        models.Note.note_id == note_id,
        models.Note.owner_user_id == current_user.user_id,
    ).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    db.delete(note)
    db.commit()
