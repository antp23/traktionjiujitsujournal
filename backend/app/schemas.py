"""Pydantic request/response contracts. These are the frozen v1 API shapes;
legacy enum spellings (`no_gi`, `win`, `loss`, `competitive`) stay accepted
so pre-auth seed data keeps serializing."""
from datetime import date, datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

SessionType = Literal["gi", "no-gi", "open_mat", "drilling", "competition_prep"]
GiNogi = Literal["gi", "no-gi", "no_gi", "both"]
Proficiency = Literal["learning", "drilling", "applying", "sharp"]
RollOutcome = Literal[
    "submission_win", "submission_loss", "draw", "points_win", "points_loss",
    "win", "loss", "competitive",
]
Belt = Literal["white", "blue", "purple", "brown", "black"]
GoalStatus = Literal["active", "completed", "paused", "archived"]
GoalVisibility = Literal["private", "shared"]


# ── Session ──────────────────────────────────────────────────────────────────

class SessionBase(BaseModel):
    date: date
    session_type: SessionType
    gym_location: Optional[str] = None
    instructor: Optional[str] = None
    duration_minutes: int = Field(default=60, ge=1, le=480)
    partners: List[str] = Field(default_factory=list)
    focus_area: Optional[str] = None
    energy_level: Optional[int] = Field(default=None, ge=1, le=10)
    notes: Optional[str] = None
    rounds_rolled: Optional[int] = Field(default=None, ge=0, le=100)
    attended: bool = True


class SessionCreate(SessionBase):
    pass


class SessionUpdate(BaseModel):
    date: Optional[date] = None
    session_type: Optional[SessionType] = None
    gym_location: Optional[str] = None
    instructor: Optional[str] = None
    duration_minutes: Optional[int] = Field(default=None, ge=1, le=480)
    partners: Optional[List[str]] = None
    focus_area: Optional[str] = None
    energy_level: Optional[int] = Field(default=None, ge=1, le=10)
    notes: Optional[str] = None
    rounds_rolled: Optional[int] = Field(default=None, ge=0, le=100)
    attended: Optional[bool] = None


class SessionResponse(SessionBase):
    model_config = ConfigDict(from_attributes=True)
    session_id: str
    created_at: datetime


# ── Technique ────────────────────────────────────────────────────────────────

class TechniqueBase(BaseModel):
    name: str
    category: str
    position: Optional[str] = None
    direction: Optional[str] = None
    gi_nogi: GiNogi = "both"
    description: Optional[str] = None
    key_details: List[str] = Field(default_factory=list)
    common_mistakes: List[str] = Field(default_factory=list)
    counters: List[str] = Field(default_factory=list)
    counters_to_counters: List[str] = Field(default_factory=list)
    video_urls: List[str] = Field(default_factory=list)
    proficiency: Proficiency = "learning"
    last_drilled: Optional[date] = None
    last_hit_in_roll: Optional[date] = None
    notes: Optional[str] = None
    source: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class TechniqueCreate(TechniqueBase):
    pass


class TechniqueUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    position: Optional[str] = None
    direction: Optional[str] = None
    gi_nogi: Optional[GiNogi] = None
    description: Optional[str] = None
    key_details: Optional[List[str]] = None
    common_mistakes: Optional[List[str]] = None
    counters: Optional[List[str]] = None
    counters_to_counters: Optional[List[str]] = None
    video_urls: Optional[List[str]] = None
    proficiency: Optional[Proficiency] = None
    last_drilled: Optional[date] = None
    last_hit_in_roll: Optional[date] = None
    notes: Optional[str] = None
    source: Optional[str] = None
    tags: Optional[List[str]] = None


class TechniqueResponse(TechniqueBase):
    model_config = ConfigDict(from_attributes=True)
    technique_id: str
    date_added: date


class LinkRequest(BaseModel):
    to_technique_id: str
    relationship_type: Literal["setup", "followup", "chain"] = "chain"


# ── Roll log ─────────────────────────────────────────────────────────────────

class RollLogBase(BaseModel):
    session_id: str
    partner: str
    duration_minutes: Optional[int] = Field(default=None, ge=1, le=120)
    gi_nogi: Literal["gi", "no-gi"]
    outcome: RollOutcome
    submission_scored: Optional[str] = None
    submission_received: Optional[str] = None
    dominant_positions_held: List[str] = Field(default_factory=list)
    dominant_positions_given: List[str] = Field(default_factory=list)
    notes: Optional[str] = None


class RollLogCreate(RollLogBase):
    pass


class RollLogUpdate(BaseModel):
    partner: Optional[str] = None
    duration_minutes: Optional[int] = Field(default=None, ge=1, le=120)
    gi_nogi: Optional[Literal["gi", "no-gi"]] = None
    outcome: Optional[RollOutcome] = None
    submission_scored: Optional[str] = None
    submission_received: Optional[str] = None
    dominant_positions_held: Optional[List[str]] = None
    dominant_positions_given: Optional[List[str]] = None
    notes: Optional[str] = None


class RollLogResponse(RollLogBase):
    model_config = ConfigDict(from_attributes=True)
    roll_id: str


# ── Rank log ─────────────────────────────────────────────────────────────────

class RankLogBase(BaseModel):
    belt: Belt
    stripes: int = Field(default=0, ge=0, le=4)
    date_awarded: date
    notes: Optional[str] = None


class RankLogCreate(RankLogBase):
    pass


class RankLogUpdate(BaseModel):
    belt: Optional[Belt] = None
    stripes: Optional[int] = Field(default=None, ge=0, le=4)
    date_awarded: Optional[date] = None
    notes: Optional[str] = None


class RankLogResponse(RankLogBase):
    model_config = ConfigDict(from_attributes=True)
    rank_id: str


# ── Note ─────────────────────────────────────────────────────────────────────

class NoteBase(BaseModel):
    title: Optional[str] = None
    content: str
    tags: List[str] = Field(default_factory=list)


class NoteCreate(NoteBase):
    pass


class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None


class NoteResponse(NoteBase):
    model_config = ConfigDict(from_attributes=True)
    note_id: str
    created_at: datetime
    updated_at: datetime


# ── Coach directory ──────────────────────────────────────────────────────────

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


# ── Auth and accounts ────────────────────────────────────────────────────────

class AuthLinkRequest(BaseModel):
    email: str


class AuthLinkResponse(BaseModel):
    message: str
    dev_token: Optional[str] = None


class AuthConsumeRequest(BaseModel):
    token: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    user_id: str
    email: str
    name: Optional[str] = None
    preferred_name: Optional[str] = None


class AuthConsumeResponse(BaseModel):
    session_token: str
    user: UserResponse


class MembershipResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    membership_id: str
    workspace_id: str
    user_id: str
    role: str
    status: str
    joined_at: datetime


class AthleteProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    profile_id: str
    user_id: str
    whatsapp_phone: Optional[str] = None
    belt: Optional[str] = None
    stripes: Optional[int] = None
    years_training: Optional[int] = None
    typical_training_frequency: Optional[str] = None
    gi_nogi_preference: Optional[str] = None
    competition_interest: Optional[str] = None
    current_focus: Optional[str] = None
    favorite_positions: List[str] = Field(default_factory=list)
    problem_positions: List[str] = Field(default_factory=list)
    injuries_or_limitations: Optional[str] = None
    updated_at: datetime


class WhatsAppIdentityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    whatsapp_identity_id: str
    user_id: str
    phone: str
    created_at: datetime


class AuthMeResponse(BaseModel):
    user: UserResponse
    memberships: List[MembershipResponse]
    profile: Optional[AthleteProfileResponse] = None


# ── Workspaces ───────────────────────────────────────────────────────────────

class WorkspaceBootstrapRequest(BaseModel):
    gym_name: str
    owner_email: str
    owner_name: Optional[str] = None


class WorkspaceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    workspace_id: str
    gym_name: str
    created_at: datetime


class InviteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    invite_id: str
    workspace_id: str
    code: str
    active: bool
    created_at: datetime


class WorkspaceBootstrapResponse(BaseModel):
    workspace: WorkspaceResponse
    owner: UserResponse
    membership: MembershipResponse
    invite: InviteResponse


class InviteLookupResponse(BaseModel):
    gym_name: str
    usable: bool


class WorkspaceJoinRequest(BaseModel):
    invite_code: str


class WorkspaceCurrentResponse(BaseModel):
    workspace: Optional[WorkspaceResponse] = None
    membership: Optional[MembershipResponse] = None
    invite: Optional[InviteResponse] = None


class AthleteProfileUpdate(BaseModel):
    name: str
    preferred_name: Optional[str] = None
    whatsapp_phone: Optional[str] = None
    belt: Optional[str] = None
    stripes: Optional[int] = Field(default=None, ge=0, le=4)
    years_training: Optional[int] = Field(default=None, ge=0, le=100)
    typical_training_frequency: Optional[str] = None
    gi_nogi_preference: Optional[str] = None
    competition_interest: Optional[str] = None
    current_focus: Optional[str] = None
    favorite_positions: List[str] = Field(default_factory=list)
    problem_positions: List[str] = Field(default_factory=list)
    injuries_or_limitations: Optional[str] = None


class AthleteProfileUpdateResponse(BaseModel):
    user: UserResponse
    profile: AthleteProfileResponse
    whatsapp_identity: Optional[WhatsAppIdentityResponse] = None


# ── Goals and sharing ────────────────────────────────────────────────────────

class GoalBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: GoalStatus = "active"
    visibility: GoalVisibility = "private"
    target_date: Optional[date] = None


class GoalCreate(GoalBase):
    pass


class GoalUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[GoalStatus] = None
    visibility: Optional[GoalVisibility] = None
    target_date: Optional[date] = None


class GoalResponse(GoalBase):
    model_config = ConfigDict(from_attributes=True)
    goal_id: str
    owner_user_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ShareThreadCreate(BaseModel):
    source_type: Literal["goal", "note"]
    source_id: str
    body: str


class ThreadMessageCreate(BaseModel):
    body: str


class ShareThreadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    thread_id: str
    workspace_id: str
    owner_user_id: str
    source_type: str
    source_id: str
    status: str
    created_at: datetime
    updated_at: datetime


class ThreadMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    message_id: str
    thread_id: str
    author_user_id: str
    body: str
    pinned_as_coach_note_id: Optional[str] = None
    created_at: datetime


class ShareThreadInboxResponse(ShareThreadResponse):
    messages: List[ThreadMessageResponse] = Field(default_factory=list)


class ShareThreadCreateResponse(BaseModel):
    thread: ShareThreadResponse
    initial_message: ThreadMessageResponse


class CoachNoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    coach_note_id: str
    owner_user_id: str
    author_user_id: Optional[str] = None
    source_message_id: Optional[str] = None
    source: str
    category: Optional[str] = None
    status: str
    content: str
    created_at: datetime


# ── Quick log ────────────────────────────────────────────────────────────────

class ParseRequest(BaseModel):
    text: str


class ParseResponse(BaseModel):
    success: bool
    action: Optional[str] = None
    message: str = ""
    data: Optional[dict] = None
