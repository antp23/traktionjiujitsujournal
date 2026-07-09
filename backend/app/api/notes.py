"""Private free-form notes."""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session as DBSession

from app import models, schemas
from app.api.deps import apply_partial_update, get_current_user, get_owned_or_404
from app.db import get_db

router = APIRouter(prefix="/notes", tags=["notes"])


def _owned_note(db: DBSession, note_id: str, user: models.User) -> models.Note:
    return get_owned_or_404(
        db, models.Note, models.Note.note_id, note_id,
        user.user_id, "Note not found",
    )


@router.get("", response_model=List[schemas.NoteResponse])
def list_notes(
    search: Optional[str] = None,
    tag: Optional[str] = None,
    current_user: models.User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    query = db.query(models.Note).filter(
        models.Note.owner_user_id == current_user.user_id
    )
    if search:
        query = query.filter(
            models.Note.content.ilike(f"%{search}%")
            | models.Note.title.ilike(f"%{search}%")
        )
    results = query.order_by(models.Note.created_at.desc()).all()
    if tag:
        results = [note for note in results if tag in (note.tags or [])]
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
    return _owned_note(db, note_id, current_user)


@router.put("/{note_id}", response_model=schemas.NoteResponse)
def update_note(
    note_id: str,
    data: schemas.NoteUpdate,
    current_user: models.User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    note = _owned_note(db, note_id, current_user)
    apply_partial_update(note, data)
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
    note = _owned_note(db, note_id, current_user)
    db.delete(note)
    db.commit()
