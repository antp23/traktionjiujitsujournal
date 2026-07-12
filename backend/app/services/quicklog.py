"""Quick-log natural language capture.

Turns a free-text message ("trained 1hr no gi, worked on guard passing")
into a session, note, or technique in the user's private journal. The
heuristics are frozen v1 behavior — deterministic keyword/regex rules, no
model in the loop.
"""
import re
from datetime import date, timedelta
from typing import Optional

from sqlalchemy.orm import Session as DBSession

from app import config, models
from app.schemas import ParseResponse

WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
MONTHS = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
          "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12}

SESSION_TRIGGERS = [
    "trained", "training", "class", "rolled", "rolled today", "just got back",
    "went to", "hit class", "mat time", "drilled", "sparred", "session",
    "just trained", "came from class", "back from",
]
NOTE_TRIGGERS = ["note", "remember", "reminder", "write down", "don't forget", "log this"]
TECHNIQUE_TRIGGERS = [
    "learned", "working on", "technique", "move", "position", "submission",
    "sweep", "guard", "pass",
]

ENERGY_WORDS = [
    (("gassed", "dead", "exhausted", "wiped"), 3),
    (("tired", "low energy", "sluggish"), 5),
    (("great", "felt good", "strong", "on fire"), 9),
    (("good", "solid", "decent"), 7),
    (("ok", "okay", "alright", "average"), 6),
]

FOCUS_PATTERN = re.compile(
    r"(?:worked on|focused on|drilling|working on|practicing)\s+([^,.]+)", re.I
)
NOTES_PATTERN = re.compile(r"notes?:?\s*(.+)", re.I)
NOTE_PREFIX_PATTERN = re.compile(r"^(note|remember|write down|log this)[:\s]*", re.I)
TECHNIQUE_NAME_PATTERN = re.compile(
    r"(?:learned|working on|drilled|practiced|hit a|trying)\s+(?:a\s+|the\s+)?([^,.]+)", re.I
)


def extract_date(text: str) -> date:
    today = date.today()
    lowered = text.lower()

    if "yesterday" in lowered:
        return today - timedelta(days=1)

    for index, day_name in enumerate(WEEKDAYS):
        if f"last {day_name}" in lowered:
            diff = (today.weekday() - index) % 7 or 7
            return today - timedelta(days=diff)

    month_match = re.search(
        r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+(\d{1,2})", lowered
    )
    if month_match:
        try:
            return date(today.year, MONTHS[month_match.group(1)[:3]], int(month_match.group(2)))
        except ValueError:
            pass

    numeric_match = re.search(r"(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?", lowered)
    if numeric_match:
        try:
            year = int(numeric_match.group(3)) if numeric_match.group(3) else today.year
            if year < 100:
                year += 2000
            return date(year, int(numeric_match.group(1)), int(numeric_match.group(2)))
        except ValueError:
            pass

    return today


def extract_duration(text: str) -> int:
    lowered = text.lower()
    hours = re.search(r"(\d+\.?\d*)\s*h(?:our|r)?s?", lowered)
    if hours:
        return int(float(hours.group(1)) * 60)
    minutes = re.search(r"(\d+)\s*min(?:ute)?s?", lowered)
    if minutes:
        return int(minutes.group(1))
    return 60


def extract_session_type(text: str) -> str:
    lowered = text.lower()
    if any(variant in lowered for variant in ("no gi", "no-gi", "nogi", "no_gi")):
        return "no-gi"
    if "gi" in lowered:
        return "gi"
    if "open mat" in lowered:
        return "open_mat"
    if "drill" in lowered:
        return "drilling"
    if "comp" in lowered:
        return "competition_prep"
    return "gi"


def extract_energy(text: str) -> Optional[int]:
    lowered = text.lower()
    for words, level in ENERGY_WORDS:
        if any(word in lowered for word in words):
            return level
    return None


def classify_intent(text: str) -> str:
    lowered = text.lower()
    if any(trigger in lowered for trigger in SESSION_TRIGGERS):
        return "session"
    if any(trigger in lowered for trigger in NOTE_TRIGGERS):
        return "note"
    if any(trigger in lowered for trigger in TECHNIQUE_TRIGGERS):
        return "technique"
    if re.search(r"\d+\s*(h|min)", lowered) or "gi" in lowered:
        return "session"
    return "unknown"


def _session_type_label(session_type: str) -> str:
    if session_type == "no-gi":
        return "No Gi"
    return session_type.replace("_", " ").title()


def _log_session(text: str, owner_user_id: str, db: DBSession) -> ParseResponse:
    session_date = extract_date(text)
    duration = extract_duration(text)
    session_type = extract_session_type(text)
    energy = extract_energy(text)

    focus_match = FOCUS_PATTERN.search(text)
    focus = focus_match.group(1).strip() if focus_match else None
    notes_match = NOTES_PATTERN.search(text)
    notes_text = notes_match.group(1).strip() if notes_match else None

    session = models.Session(
        owner_user_id=owner_user_id,
        date=session_date,
        session_type=session_type,
        duration_minutes=duration,
        focus_area=focus,
        notes=notes_text or text,
        energy_level=energy,
        attended=True,
        gym_location=config.QUICK_LOG_DEFAULT_GYM,
    )
    db.add(session)
    db.flush()

    focus_str = f" — {focus}" if focus else ""
    energy_str = f" | Energy: {energy}/10" if energy else ""
    return ParseResponse(
        success=True,
        action="session_logged",
        message=(
            f"Session logged: {_session_type_label(session_type)}, {duration}min "
            f"on {session_date.strftime('%b %-d')}{focus_str}{energy_str}"
        ),
        data={"session_id": session.session_id, "date": str(session_date)},
    )


def _log_note(text: str, owner_user_id: str, db: DBSession) -> ParseResponse:
    note_text = NOTE_PREFIX_PATTERN.sub("", text).strip()
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
        message=f'Note saved: "{(note_text or text)[:80]}"',
        data={"note_id": note.note_id},
    )


def _log_technique(text: str, owner_user_id: str, db: DBSession) -> ParseResponse:
    name_match = TECHNIQUE_NAME_PATTERN.search(text)
    name = name_match.group(1).strip() if name_match else text[:60]

    existing = (
        db.query(models.Technique)
        .filter(
            models.Technique.owner_user_id == owner_user_id,
            models.Technique.name.ilike(f"%{name}%"),
        )
        .first()
    )
    if existing:
        return ParseResponse(
            success=True,
            action="technique_exists",
            message=(
                f'"{existing.name}" is already in your library '
                f"(proficiency: {existing.proficiency})."
            ),
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
        message=f'Technique added: "{name.title()}" — marked as Learning',
        data={"technique_id": technique.technique_id},
    )


def _log_raw_capture(text: str, owner_user_id: str, db: DBSession) -> ParseResponse:
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


def parse_text_to_private_journal(
    text: str, owner_user_id: str, db: DBSession
) -> ParseResponse:
    """Route free text into the owner's private journal. Flushes but does not
    commit — the caller controls the transaction."""
    text = text.strip()
    if not text:
        return ParseResponse(success=False, message="Empty input.")

    intent = classify_intent(text)
    if intent == "session":
        return _log_session(text, owner_user_id, db)
    if intent == "note":
        return _log_note(text, owner_user_id, db)
    if intent == "technique":
        return _log_technique(text, owner_user_id, db)
    return _log_raw_capture(text, owner_user_id, db)
