from typing import List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession, selectinload

import models
import schemas
from database import get_db
from routers.auth import get_current_user

router = APIRouter(prefix="/sharing", tags=["sharing"])


def _current_membership(db: DBSession, user_id: str):
    return (
        db.query(models.Membership)
        .filter(
            models.Membership.user_id == user_id,
            models.Membership.status == "active",
        )
        .first()
    )


def _can_see_thread(db: DBSession, user: models.User, thread: models.ShareThread) -> bool:
    if thread.owner_user_id == user.user_id:
        return True
    membership = (
        db.query(models.Membership)
        .filter(
            models.Membership.user_id == user.user_id,
            models.Membership.workspace_id == thread.workspace_id,
            models.Membership.status == "active",
            models.Membership.role.in_(("owner", "coach")),
        )
        .first()
    )
    return membership is not None


def _assert_owned_source(
    db: DBSession,
    user: models.User,
    source_type: str,
    source_id: str,
):
    if source_type == "goal":
        goal = (
            db.query(models.Goal)
            .filter(
                models.Goal.goal_id == source_id,
                models.Goal.owner_user_id == user.user_id,
            )
            .first()
        )
        if not goal:
            raise HTTPException(status_code=404, detail="Goal not found")
        goal.visibility = "shared"
        return

    note = db.query(models.Note).filter(models.Note.note_id == source_id).first()
    if not note or note.owner_user_id not in (None, user.user_id):
        raise HTTPException(status_code=404, detail="Note not found")
    note.owner_user_id = user.user_id


@router.post("/threads", response_model=schemas.ShareThreadCreateResponse, status_code=201)
def create_thread(
    data: schemas.ShareThreadCreate,
    current_user: models.User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    membership = _current_membership(db, current_user.user_id)
    if not membership:
        raise HTTPException(status_code=400, detail="Join a workspace before sharing")

    _assert_owned_source(db, current_user, data.source_type, data.source_id)
    thread = models.ShareThread(
        workspace_id=membership.workspace_id,
        owner_user_id=current_user.user_id,
        source_type=data.source_type,
        source_id=data.source_id,
    )
    db.add(thread)
    db.flush()
    message = models.ThreadMessage(
        thread_id=thread.thread_id,
        author_user_id=current_user.user_id,
        body=data.body,
    )
    db.add(message)
    thread.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(thread)
    db.refresh(message)
    return {"thread": thread, "initial_message": message}


@router.get("/inbox", response_model=List[schemas.ShareThreadInboxResponse])
def inbox(
    current_user: models.User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    memberships = (
        db.query(models.Membership)
        .filter(
            models.Membership.user_id == current_user.user_id,
            models.Membership.status == "active",
        )
        .all()
    )
    coach_workspace_ids = [
        membership.workspace_id
        for membership in memberships
        if membership.role in ("owner", "coach")
    ]
    if coach_workspace_ids:
        return (
            db.query(models.ShareThread)
            .options(selectinload(models.ShareThread.messages))
            .filter(models.ShareThread.workspace_id.in_(coach_workspace_ids))
            .order_by(models.ShareThread.updated_at.desc())
            .all()
        )
    return (
        db.query(models.ShareThread)
        .options(selectinload(models.ShareThread.messages))
        .filter(models.ShareThread.owner_user_id == current_user.user_id)
        .order_by(models.ShareThread.updated_at.desc())
        .all()
    )


@router.post(
    "/threads/{thread_id}/messages",
    response_model=schemas.ThreadMessageResponse,
    status_code=201,
)
def create_message(
    thread_id: str,
    data: schemas.ThreadMessageCreate,
    current_user: models.User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    thread = db.query(models.ShareThread).filter(models.ShareThread.thread_id == thread_id).first()
    if not thread or not _can_see_thread(db, current_user, thread):
        raise HTTPException(status_code=404, detail="Thread not found")
    message = models.ThreadMessage(
        thread_id=thread.thread_id,
        author_user_id=current_user.user_id,
        body=data.body,
    )
    db.add(message)
    thread.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(message)
    return message


@router.post(
    "/messages/{message_id}/pin",
    response_model=schemas.CoachNoteResponse,
    status_code=201,
)
def pin_message(
    message_id: str,
    current_user: models.User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    message = (
        db.query(models.ThreadMessage)
        .filter(models.ThreadMessage.message_id == message_id)
        .first()
    )
    if not message or not _can_see_thread(db, current_user, message.thread):
        raise HTTPException(status_code=404, detail="Message not found")

    if message.pinned_as_coach_note_id:
        existing = (
            db.query(models.CoachNote)
            .filter(models.CoachNote.coach_note_id == message.pinned_as_coach_note_id)
            .first()
        )
        if existing:
            return existing

    coach_note = models.CoachNote(
        owner_user_id=message.thread.owner_user_id,
        author_user_id=message.author_user_id,
        source_message_id=message.message_id,
        source="coach",
        content=message.body,
    )
    db.add(coach_note)
    db.flush()
    message.pinned_as_coach_note_id = coach_note.coach_note_id
    db.commit()
    db.refresh(coach_note)
    return coach_note
