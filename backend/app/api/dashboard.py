"""Aggregate dashboard payload, composed from the same services the
individual endpoints use."""
import random

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session as DBSession

from app import models
from app.api.deps import get_current_user
from app.db import get_db
from app.services import stats

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard")
def dashboard(
    current_user: models.User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    owner_id = current_user.user_id

    current_rank = (
        db.query(models.RankLog)
        .filter(models.RankLog.owner_user_id == owner_id)
        .order_by(models.RankLog.date_awarded.desc())
        .first()
    )

    techniques = (
        db.query(models.Technique)
        .filter(models.Technique.owner_user_id == owner_id)
        .all()
    )
    proficiency_counts: dict[str, int] = {}
    for technique in techniques:
        proficiency_counts[technique.proficiency] = (
            proficiency_counts.get(technique.proficiency, 0) + 1
        )

    recent_sessions = (
        db.query(models.Session)
        .filter(models.Session.owner_user_id == owner_id)
        .order_by(models.Session.date.desc())
        .limit(5)
        .all()
    )

    spotlight_candidates = [
        t for t in techniques if t.proficiency in ("learning", "drilling")
    ] or techniques
    spotlight = random.choice(spotlight_candidates) if spotlight_candidates else None

    return {
        "session_stats": stats.session_stats_for_owner(db, owner_id),
        "current_rank": {
            "belt": current_rank.belt if current_rank else None,
            "stripes": current_rank.stripes if current_rank else 0,
            "date_awarded": str(current_rank.date_awarded) if current_rank else None,
        },
        "technique_counts": proficiency_counts,
        "total_techniques": len(techniques),
        "recent_sessions": [
            {
                "session_id": session.session_id,
                "date": str(session.date),
                "session_type": session.session_type,
                "duration_minutes": session.duration_minutes,
                "focus_area": session.focus_area,
                "attended": session.attended,
            }
            for session in recent_sessions
        ],
        "roll_stats": stats.roll_stats_for_owner(db, owner_id),
        "spotlight": {
            "technique_id": spotlight.technique_id,
            "name": spotlight.name,
            "category": spotlight.category,
            "proficiency": spotlight.proficiency,
            "position": spotlight.position,
        } if spotlight else None,
    }
