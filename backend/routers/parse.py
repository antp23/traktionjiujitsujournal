from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session as DBSession
from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
import re
import models
from database import get_db
from routers.auth import get_current_user

router = APIRouter(prefix="/parse", tags=["parse"])

class ParseRequest(BaseModel):
    text: str

class ParseResponse(BaseModel):
    success: bool
    action: Optional[str] = None
    message: str = ""
    data: Optional[dict] = None

# --- Helpers ---

def extract_date(text: str) -> date:
    today = date.today()
    t = text.lower()

    if "yesterday" in t:
        from datetime import timedelta
        return today - timedelta(days=1)

    # "last monday" etc
    days = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]
    for i, day in enumerate(days):
        if f"last {day}" in t:
            from datetime import timedelta
            diff = (today.weekday() - i) % 7 or 7
            return today - timedelta(days=diff)

    # Explicit dates like "April 2" or "4/2"
    m = re.search(r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+(\d{1,2})', t)
    if m:
        month_map = {"jan":1,"feb":2,"mar":3,"apr":4,"may":5,"jun":6,"jul":7,"aug":8,"sep":9,"oct":10,"nov":11,"dec":12}
        month = month_map[m.group(1)[:3]]
        day_num = int(m.group(2))
        try:
            return date(today.year, month, day_num)
        except:
            pass

    m = re.search(r'(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?', t)
    if m:
        try:
            year = int(m.group(3)) if m.group(3) else today.year
            if year < 100: year += 2000
            return date(year, int(m.group(1)), int(m.group(2)))
        except:
            pass

    return today

def extract_duration(text: str) -> int:
    t = text.lower()
    m = re.search(r'(\d+\.?\d*)\s*h(?:our|r)?s?', t)
    if m:
        return int(float(m.group(1)) * 60)
    m = re.search(r'(\d+)\s*min(?:ute)?s?', t)
    if m:
        return int(m.group(1))
    if re.search(r'\bhour\b', t):
        return 60
    return 60  # default

def extract_session_type(text: str) -> str:
    t = text.lower()
    if any(x in t for x in ["no gi", "no-gi", "nogi", "no_gi"]):
        return "no-gi"
    if "gi" in t:
        return "gi"
    if "open mat" in t:
        return "open_mat"
    if "drill" in t:
        return "drilling"
    if "comp" in t:
        return "competition_prep"
    return "gi"  # default

def extract_energy(text: str) -> Optional[int]:
    t = text.lower()
    if any(x in t for x in ["gassed", "dead", "exhausted", "wiped"]):
        return 3
    if any(x in t for x in ["tired", "low energy", "sluggish"]):
        return 5
    if any(x in t for x in ["great", "felt good", "strong", "on fire"]):
        return 9
    if any(x in t for x in ["good", "solid", "decent"]):
        return 7
    if any(x in t for x in ["ok", "okay", "alright", "average"]):
        return 6
    return None

def classify_intent(text: str) -> str:
    t = text.lower()

    session_triggers = [
        "trained", "training", "class", "rolled", "rolled today", "just got back",
        "went to", "hit class", "mat time", "drilled", "sparred", "session",
        "just trained", "came from class", "back from"
    ]
    note_triggers = ["note", "remember", "reminder", "write down", "don't forget", "log this"]
    technique_triggers = ["learned", "working on", "technique", "move", "position", "submission", "sweep", "guard", "pass"]

    if any(x in t for x in session_triggers):
        return "session"
    if any(x in t for x in note_triggers):
        return "note"
    if any(x in t for x in technique_triggers):
        return "technique"

    # Fallback: if it mentions gi/no-gi or duration, treat as session
    if re.search(r'\d+\s*(h|min)', t) or "gi" in t:
        return "session"

    return "unknown"


def parse_text_to_private_journal(
    text: str,
    owner_user_id: str,
    db: DBSession,
) -> ParseResponse:
    text = text.strip()
    if not text:
        return ParseResponse(success=False, message="Empty input.")

    intent = classify_intent(text)

    if intent == "session":
        session_date = extract_date(text)
        duration = extract_duration(text)
        session_type = extract_session_type(text)
        energy = extract_energy(text)
        focus = None
        notes_text = None
        m = re.search(r'(?:worked on|focused on|drilling|working on|practicing)\s+([^,.]+)', text, re.I)
        if m:
            focus = m.group(1).strip()
        m2 = re.search(r'notes?:?\s*(.+)', text, re.I)
        if m2:
            notes_text = m2.group(1).strip()

        session = models.Session(
            owner_user_id=owner_user_id,
            date=session_date,
            session_type=session_type,
            duration_minutes=duration,
            focus_area=focus,
            notes=notes_text or text,
            energy_level=energy,
            attended=True,
            gym_location="Traktion Jiu Jitsu Academy",
        )
        db.add(session)
        db.flush()

        type_label = "No Gi" if session_type == "no-gi" else session_type.replace("_", " ").title()
        focus_str = f" — {focus}" if focus else ""
        energy_str = f" | Energy: {energy}/10" if energy else ""
        return ParseResponse(
            success=True,
            action="session_logged",
            message=f"Session logged: {type_label}, {duration}min on {session_date.strftime('%b %-d')}{focus_str}{energy_str}",
            data={"session_id": session.session_id, "date": str(session_date)},
        )

    if intent == "note":
        note_text = re.sub(r'^(note|remember|write down|log this)[:\s]*', '', text, flags=re.I).strip()
        note = models.Note(
            owner_user_id=owner_user_id,
            content=note_text or text,
            tags=["quick-log"],
        )
        db.add(note)
        db.flush()
        return ParseResponse(
            success=True,
            action="note_logged",
            message=f"Note saved: \"{(note_text or text)[:80]}\"",
            data={"note_id": note.note_id},
        )

    if intent == "technique":
        m = re.search(r'(?:learned|working on|drilled|practiced|hit a|trying)\s+(?:a\s+|the\s+)?([^,.]+)', text, re.I)
        name = m.group(1).strip() if m else text[:60]
        existing = db.query(models.Technique).filter(
            models.Technique.owner_user_id == owner_user_id,
            models.Technique.name.ilike(f"%{name}%"),
        ).first()

        if existing:
            return ParseResponse(
                success=True,
                action="technique_exists",
                message=f"\"{existing.name}\" is already in your library (proficiency: {existing.proficiency}).",
                data={"technique_id": existing.technique_id},
            )

        technique = models.Technique(
            owner_user_id=owner_user_id,
            name=name.title(),
            category="General",
            proficiency="learning",
            notes=text,
        )
        db.add(technique)
        db.flush()
        return ParseResponse(
            success=True,
            action="technique_logged",
            message=f"Technique added: \"{name.title()}\" — marked as Learning",
            data={"technique_id": technique.technique_id},
        )

    note = models.Note(
        owner_user_id=owner_user_id,
        title="Quick Log capture",
        content=text,
        tags=["quick-log", "unparsed"],
    )
    db.add(note)
    db.flush()
    return ParseResponse(
        success=True,
        action="raw_capture_logged",
        message="Saved as a private Quick Log journal capture.",
        data={"note_id": note.note_id},
    )

# --- Routes ---

@router.post("", response_model=ParseResponse)
def parse_input(
    body: ParseRequest,
    current_user: models.User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    result = parse_text_to_private_journal(body.text, current_user.user_id, db)
    db.commit()
    return result
