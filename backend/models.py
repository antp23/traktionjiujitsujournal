"""Back-compat shim: ORM models live in app.models."""
from app.models import (
    AthleteProfile, AuthToken, Coach, CoachNote, Goal, GymWorkspace,
    InboundMessage, InviteLink, LinkedTechnique, Membership, Note, OuraDaily,
    OuraToken, RankLog, RollLog, Session, SessionTechnique, ShareThread,
    Technique, ThreadMessage, User, WhatsAppIdentity, new_uuid,
)
from app.db import Base

__all__ = [
    "AthleteProfile", "AuthToken", "Base", "Coach", "CoachNote", "Goal",
    "GymWorkspace", "InboundMessage", "InviteLink", "LinkedTechnique",
    "Membership", "Note", "OuraDaily", "OuraToken", "RankLog", "RollLog",
    "Session", "SessionTechnique", "ShareThread", "Technique",
    "ThreadMessage", "User", "WhatsAppIdentity", "new_uuid",
]
