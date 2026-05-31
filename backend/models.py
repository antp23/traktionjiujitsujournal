import uuid
from datetime import date, datetime
from sqlalchemy import Column, String, Integer, Boolean, Text, Date, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from database import Base

def new_uuid():
    return str(uuid.uuid4())

class Session(Base):
    __tablename__ = "sessions"

    session_id = Column(String, primary_key=True, default=new_uuid)
    owner_user_id = Column(String, ForeignKey("users.user_id"), nullable=True)
    date = Column(Date, nullable=False)
    session_type = Column(String, nullable=False)  # gi, no-gi, open_mat, drilling, competition_prep
    gym_location = Column(String, nullable=True)
    instructor = Column(String, nullable=True)
    duration_minutes = Column(Integer, nullable=False, default=60)
    partners = Column(JSON, default=list)
    focus_area = Column(String, nullable=True)
    energy_level = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)
    rounds_rolled = Column(Integer, nullable=True)
    attended = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    rolls = relationship("RollLog", back_populates="session", cascade="all, delete-orphan")
    session_techniques = relationship("SessionTechnique", back_populates="session", cascade="all, delete-orphan")


class Technique(Base):
    __tablename__ = "techniques"

    technique_id = Column(String, primary_key=True, default=new_uuid)
    owner_user_id = Column(String, ForeignKey("users.user_id"), nullable=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    position = Column(String, nullable=True)
    direction = Column(String, nullable=True)  # offensive, defensive, transition
    gi_nogi = Column(String, default="both")   # gi, no-gi, both
    description = Column(Text, nullable=True)
    key_details = Column(JSON, default=list)
    common_mistakes = Column(JSON, default=list)
    counters = Column(JSON, default=list)
    counters_to_counters = Column(JSON, default=list)
    video_urls = Column(JSON, default=list)
    proficiency = Column(String, default="learning")  # learning, drilling, applying, sharp
    last_drilled = Column(Date, nullable=True)
    last_hit_in_roll = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    date_added = Column(Date, default=date.today)
    source = Column(String, nullable=True)
    tags = Column(JSON, default=list)

    session_techniques = relationship("SessionTechnique", back_populates="technique")
    links_from = relationship("LinkedTechnique", foreign_keys="LinkedTechnique.from_technique_id", back_populates="from_technique", cascade="all, delete-orphan")
    links_to = relationship("LinkedTechnique", foreign_keys="LinkedTechnique.to_technique_id", back_populates="to_technique", cascade="all, delete-orphan")


class SessionTechnique(Base):
    __tablename__ = "session_techniques"

    id = Column(String, primary_key=True, default=new_uuid)
    session_id = Column(String, ForeignKey("sessions.session_id"), nullable=False)
    technique_id = Column(String, ForeignKey("techniques.technique_id"), nullable=False)

    session = relationship("Session", back_populates="session_techniques")
    technique = relationship("Technique", back_populates="session_techniques")


class LinkedTechnique(Base):
    __tablename__ = "linked_techniques"

    id = Column(String, primary_key=True, default=new_uuid)
    from_technique_id = Column(String, ForeignKey("techniques.technique_id"), nullable=False)
    to_technique_id = Column(String, ForeignKey("techniques.technique_id"), nullable=False)
    relationship_type = Column(String, default="chain")  # setup, followup, chain

    from_technique = relationship("Technique", foreign_keys=[from_technique_id], back_populates="links_from")
    to_technique = relationship("Technique", foreign_keys=[to_technique_id], back_populates="links_to")


class RollLog(Base):
    __tablename__ = "roll_logs"

    roll_id = Column(String, primary_key=True, default=new_uuid)
    owner_user_id = Column(String, ForeignKey("users.user_id"), nullable=True)
    session_id = Column(String, ForeignKey("sessions.session_id"), nullable=False)
    partner = Column(String, nullable=False)
    duration_minutes = Column(Integer, nullable=True)
    gi_nogi = Column(String, nullable=False)
    outcome = Column(String, nullable=False)  # submission_win, submission_loss, draw, points_win, points_loss
    submission_scored = Column(String, nullable=True)
    submission_received = Column(String, nullable=True)
    dominant_positions_held = Column(JSON, default=list)
    dominant_positions_given = Column(JSON, default=list)
    notes = Column(Text, nullable=True)

    session = relationship("Session", back_populates="rolls")


class RankLog(Base):
    __tablename__ = "rank_logs"

    rank_id = Column(String, primary_key=True, default=new_uuid)
    owner_user_id = Column(String, ForeignKey("users.user_id"), nullable=True)
    belt = Column(String, nullable=False)
    stripes = Column(Integer, default=0)
    date_awarded = Column(Date, nullable=False)
    notes = Column(Text, nullable=True)


class Note(Base):
    __tablename__ = "notes"

    note_id = Column(String, primary_key=True, default=new_uuid)
    owner_user_id = Column(String, ForeignKey("users.user_id"), nullable=True)
    title = Column(String, nullable=True)
    content = Column(Text, nullable=False)
    tags = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class InboundMessage(Base):
    __tablename__ = "inbound_messages"

    inbound_message_id = Column(String, primary_key=True, default=new_uuid)
    provider = Column(String, nullable=False)
    provider_message_id = Column(String, nullable=False, unique=True, index=True)
    from_phone = Column(String, nullable=False, index=True)
    to_phone = Column(String, nullable=True)
    owner_user_id = Column(String, ForeignKey("users.user_id"), nullable=True)
    raw_body = Column(Text, nullable=False)
    parsed_status = Column(String, nullable=False, default="received")
    parse_action = Column(String, nullable=True)
    parse_message = Column(Text, nullable=True)
    received_at = Column(DateTime, default=datetime.utcnow)


class OuraToken(Base):
    __tablename__ = "oura_tokens"

    id = Column(Integer, primary_key=True, default=1)
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class OuraDaily(Base):
    __tablename__ = "oura_daily"

    id = Column(String, primary_key=True, default=new_uuid)
    date = Column(String, nullable=False, unique=True)  # YYYY-MM-DD
    readiness_score = Column(Integer, nullable=True)
    sleep_score = Column(Integer, nullable=True)
    hrv_avg = Column(Integer, nullable=True)
    resting_hr = Column(Integer, nullable=True)
    total_sleep_minutes = Column(Integer, nullable=True)
    temperature_deviation = Column(String, nullable=True)
    raw = Column(Text, nullable=True)
    synced_at = Column(DateTime, default=datetime.utcnow)


class User(Base):
    __tablename__ = "users"

    user_id = Column(String, primary_key=True, default=new_uuid)
    email = Column(String, nullable=False, unique=True, index=True)
    name = Column(String, nullable=True)
    preferred_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    memberships = relationship("Membership", back_populates="user", cascade="all, delete-orphan")
    profile = relationship("AthleteProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    whatsapp_identity = relationship("WhatsAppIdentity", back_populates="user", uselist=False, cascade="all, delete-orphan")
    goals = relationship("Goal", back_populates="owner", cascade="all, delete-orphan")


class AuthToken(Base):
    __tablename__ = "auth_tokens"

    token = Column(String, primary_key=True, default=new_uuid)
    email = Column(String, nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=True)
    token_type = Column(String, nullable=False, default="magic_link")
    consumed_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")


class GymWorkspace(Base):
    __tablename__ = "gym_workspaces"

    workspace_id = Column(String, primary_key=True, default=new_uuid)
    gym_name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    memberships = relationship("Membership", back_populates="workspace", cascade="all, delete-orphan")
    invite_links = relationship("InviteLink", back_populates="workspace", cascade="all, delete-orphan")


class Membership(Base):
    __tablename__ = "memberships"

    membership_id = Column(String, primary_key=True, default=new_uuid)
    workspace_id = Column(String, ForeignKey("gym_workspaces.workspace_id"), nullable=False)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    role = Column(String, nullable=False, default="athlete")
    status = Column(String, nullable=False, default="active")
    joined_at = Column(DateTime, default=datetime.utcnow)

    workspace = relationship("GymWorkspace", back_populates="memberships")
    user = relationship("User", back_populates="memberships")


class InviteLink(Base):
    __tablename__ = "invite_links"

    invite_id = Column(String, primary_key=True, default=new_uuid)
    workspace_id = Column(String, ForeignKey("gym_workspaces.workspace_id"), nullable=False)
    code = Column(String, nullable=False, unique=True, index=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    workspace = relationship("GymWorkspace", back_populates="invite_links")


class AthleteProfile(Base):
    __tablename__ = "athlete_profiles"

    profile_id = Column(String, primary_key=True, default=new_uuid)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False, unique=True)
    whatsapp_phone = Column(String, nullable=True)
    belt = Column(String, nullable=True)
    stripes = Column(Integer, nullable=True)
    years_training = Column(Integer, nullable=True)
    typical_training_frequency = Column(String, nullable=True)
    gi_nogi_preference = Column(String, nullable=True)
    competition_interest = Column(String, nullable=True)
    current_focus = Column(String, nullable=True)
    favorite_positions = Column(JSON, default=list)
    problem_positions = Column(JSON, default=list)
    injuries_or_limitations = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="profile")


class WhatsAppIdentity(Base):
    __tablename__ = "whatsapp_identities"

    whatsapp_identity_id = Column(String, primary_key=True, default=new_uuid)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False, unique=True)
    phone = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="whatsapp_identity")


class Goal(Base):
    __tablename__ = "goals"

    goal_id = Column(String, primary_key=True, default=new_uuid)
    owner_user_id = Column(String, ForeignKey("users.user_id"), nullable=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="active")
    visibility = Column(String, nullable=False, default="private")
    target_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("User", back_populates="goals")


class ShareThread(Base):
    __tablename__ = "share_threads"

    thread_id = Column(String, primary_key=True, default=new_uuid)
    workspace_id = Column(String, ForeignKey("gym_workspaces.workspace_id"), nullable=False)
    owner_user_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    source_type = Column(String, nullable=False)
    source_id = Column(String, nullable=False)
    status = Column(String, nullable=False, default="open")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    messages = relationship(
        "ThreadMessage",
        back_populates="thread",
        cascade="all, delete-orphan",
        order_by="ThreadMessage.created_at",
    )


class ThreadMessage(Base):
    __tablename__ = "thread_messages"

    message_id = Column(String, primary_key=True, default=new_uuid)
    thread_id = Column(String, ForeignKey("share_threads.thread_id"), nullable=False)
    author_user_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    body = Column(Text, nullable=False)
    pinned_as_coach_note_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    thread = relationship("ShareThread", back_populates="messages")


class CoachNote(Base):
    __tablename__ = "coach_notes"

    coach_note_id = Column(String, primary_key=True, default=new_uuid)
    owner_user_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    author_user_id = Column(String, ForeignKey("users.user_id"), nullable=True)
    source_message_id = Column(String, ForeignKey("thread_messages.message_id"), nullable=True)
    source = Column(String, nullable=False, default="coach")
    category = Column(String, nullable=True)
    status = Column(String, nullable=False, default="active")
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
