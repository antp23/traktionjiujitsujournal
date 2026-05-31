from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from datetime import date, datetime
import uuid
from database import get_db
from models import Base
from sqlalchemy import Column, String, Text, Date, DateTime, JSON

# Inline model since it's small
from database import engine
from sqlalchemy.orm import DeclarativeBase

class Coach(Base):
    __tablename__ = "coaches"
    __table_args__ = {'extend_existing': True}

    coach_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    gym = Column(String, nullable=True)
    belt = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    date_added = Column(Date, default=date.today)

# Create table if not exists
Base.metadata.create_all(bind=engine)

class CoachBase(BaseModel):
    name: str
    gym: Optional[str] = None
    belt: Optional[str] = None
    notes: Optional[str] = None

class CoachCreate(CoachBase):
    pass

class CoachUpdate(BaseModel):
    name: Optional[str] = None
    gym: Optional[str] = None
    belt: Optional[str] = None
    notes: Optional[str] = None

class CoachResponse(CoachBase):
    model_config = ConfigDict(from_attributes=True)
    coach_id: str
    date_added: date

router = APIRouter(prefix="/coaches", tags=["coaches"])

@router.get("", response_model=List[CoachResponse])
def list_coaches(db: DBSession = Depends(get_db)):
    return db.query(Coach).all()

@router.post("", response_model=CoachResponse, status_code=201)
def create_coach(data: CoachCreate, db: DBSession = Depends(get_db)):
    coach = Coach(**data.model_dump())
    db.add(coach)
    db.commit()
    db.refresh(coach)
    return coach

@router.get("/{coach_id}", response_model=CoachResponse)
def get_coach(coach_id: str, db: DBSession = Depends(get_db)):
    coach = db.query(Coach).filter(Coach.coach_id == coach_id).first()
    if not coach:
        raise HTTPException(status_code=404, detail="Coach not found")
    return coach

@router.put("/{coach_id}", response_model=CoachResponse)
def update_coach(coach_id: str, data: CoachUpdate, db: DBSession = Depends(get_db)):
    coach = db.query(Coach).filter(Coach.coach_id == coach_id).first()
    if not coach:
        raise HTTPException(status_code=404, detail="Coach not found")
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(coach, k, v)
    db.commit()
    db.refresh(coach)
    return coach

@router.delete("/{coach_id}", status_code=204)
def delete_coach(coach_id: str, db: DBSession = Depends(get_db)):
    coach = db.query(Coach).filter(Coach.coach_id == coach_id).first()
    if not coach:
        raise HTTPException(status_code=404, detail="Coach not found")
    db.delete(coach)
    db.commit()
