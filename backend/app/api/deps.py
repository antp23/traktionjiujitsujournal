"""Shared FastAPI dependencies and ownership helpers."""
from typing import Type, TypeVar

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session as DBSession

from app import models, security
from app.db import get_db

ModelT = TypeVar("ModelT")


def get_current_user(
    x_session_token: str = Header(default=None),
    db: DBSession = Depends(get_db),
) -> models.User:
    return security.resolve_session(db, x_session_token).user


def get_owned_or_404(
    db: DBSession,
    model: Type[ModelT],
    id_column,
    entity_id: str,
    owner_user_id: str,
    detail: str,
) -> ModelT:
    """Fetch a row by id scoped to its owner; missing and foreign rows are
    indistinguishable (404) so ids never leak across accounts."""
    row = (
        db.query(model)
        .filter(id_column == entity_id, model.owner_user_id == owner_user_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail=detail)
    return row


def apply_partial_update(row, data) -> None:
    """Copy only client-supplied fields onto the ORM row (PUT-as-patch)."""
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
