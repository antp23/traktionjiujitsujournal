from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession

import models
import schemas
from database import get_db
from routers.auth import get_current_user

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
    goal = (
        db.query(models.Goal)
        .filter(
            models.Goal.goal_id == goal_id,
            models.Goal.owner_user_id == current_user.user_id,
        )
        .first()
    )
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(goal, field, value)
    goal.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(goal)
    return goal
