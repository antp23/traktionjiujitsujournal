"""Quick-log endpoint: free text in, journal entry out."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session as DBSession

from app import models, schemas
from app.api.deps import get_current_user
from app.db import get_db
from app.services.quicklog import parse_text_to_private_journal

router = APIRouter(prefix="/parse", tags=["parse"])


@router.post("", response_model=schemas.ParseResponse)
def parse_input(
    body: schemas.ParseRequest,
    current_user: models.User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    result = parse_text_to_private_journal(body.text, current_user.user_id, db)
    db.commit()
    return result
