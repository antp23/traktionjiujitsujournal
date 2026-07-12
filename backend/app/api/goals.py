"""Training goals. Deliberately no DELETE — goals are archived via status."""
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session as DBSession

from app import models, schemas
from app.api.deps import apply_partial_update, get_current_user, get_owned_or_404
from app.db import get_db

router = APIRouter(prefix="/goals", tags=["goals"])


@router.get("", response_model=List[schemas.GoalResponse])
def list_goals(
    current_user: models.User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    return (
        db.query(models.Goal)
        .filter(models.Goal.owner_user_id == current_user.user_id)
        .order_by(models.Goal.created_at.desc())
        .all()
    )


@router.post("", response_model=schemas.GoalResponse, status_code=201)
def create_goal(
    data: schemas.GoalCreate,
    current_user: models.User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    goal = models.Goal(owner_user_id=current_user.user_id, **data.model_dump())
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


@router.put("/{goal_id}", response_model=schemas.GoalResponse)
def update_goal(
    goal_id: str,
    data: schemas.GoalUpdate,
    current_user: models.User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    goal = get_owned_or_404(
        db, models.Goal, models.Goal.goal_id, goal_id,
        current_user.user_id, "Goal not found",
    )
    apply_partial_update(goal, data)
    goal.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(goal)
    return goal
