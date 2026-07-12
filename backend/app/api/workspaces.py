"""Gym workspace: bootstrap, invites, enrollment, athlete profile."""
import secrets

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession

from app import models, schemas, security
from app.api.deps import get_current_user
from app.db import get_db

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


def _new_invite_code() -> str:
    return secrets.token_urlsafe(8)


def _active_invite(db: DBSession, workspace_id: str) -> models.InviteLink | None:
    return (
        db.query(models.InviteLink)
        .filter(
            models.InviteLink.workspace_id == workspace_id,
            models.InviteLink.active.is_(True),
        )
        .first()
    )


@router.post("/bootstrap", response_model=schemas.WorkspaceBootstrapResponse)
def bootstrap_workspace(
    data: schemas.WorkspaceBootstrapRequest,
    db: DBSession = Depends(get_db),
):
    """Create (or idempotently return) the single gym workspace, its owner
    account, owner membership, and an active invite code."""
    workspace = db.query(models.GymWorkspace).first()
    owner_email = security.normalize_email(data.owner_email)
    owner = db.query(models.User).filter(models.User.email == owner_email).first()
    if not owner:
        owner = models.User(email=owner_email)
        db.add(owner)
        db.flush()
    owner.name = data.owner_name
    owner.preferred_name = data.owner_name

    if not workspace:
        workspace = models.GymWorkspace(gym_name=data.gym_name)
        db.add(workspace)
        db.flush()

    membership = (
        db.query(models.Membership)
        .filter(
            models.Membership.workspace_id == workspace.workspace_id,
            models.Membership.user_id == owner.user_id,
        )
        .first()
    )
    if not membership:
        membership = models.Membership(
            workspace_id=workspace.workspace_id,
            user_id=owner.user_id,
            role="owner",
            status="active",
        )
        db.add(membership)
        db.flush()

    invite = _active_invite(db, workspace.workspace_id)
    if not invite:
        invite = models.InviteLink(
            workspace_id=workspace.workspace_id, code=_new_invite_code()
        )
        db.add(invite)

    db.commit()
    for row in (workspace, owner, membership, invite):
        db.refresh(row)
    return {
        "workspace": workspace,
        "owner": owner,
        "membership": membership,
        "invite": invite,
    }


@router.get("/invites/{code}", response_model=schemas.InviteLookupResponse)
def lookup_invite(code: str, db: DBSession = Depends(get_db)):
    invite = db.query(models.InviteLink).filter(models.InviteLink.code == code).first()
    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found")
    return {"gym_name": invite.workspace.gym_name, "usable": bool(invite.active)}


@router.get("/current", response_model=schemas.WorkspaceCurrentResponse)
def current_workspace(
    current_user: models.User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    membership = (
        db.query(models.Membership)
        .filter(
            models.Membership.user_id == current_user.user_id,
            models.Membership.status == "active",
        )
        .first()
    )
    if not membership:
        return {"workspace": None, "membership": None, "invite": None}

    invite = None
    if membership.role in ("owner", "coach"):
        invite = _active_invite(db, membership.workspace_id)
    return {
        "workspace": membership.workspace,
        "membership": membership,
        "invite": invite,
    }


@router.post("/join", response_model=schemas.MembershipResponse)
def join_workspace(
    data: schemas.WorkspaceJoinRequest,
    current_user: models.User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    invite = (
        db.query(models.InviteLink)
        .filter(
            models.InviteLink.code == data.invite_code,
            models.InviteLink.active.is_(True),
        )
        .first()
    )
    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found")

    membership = (
        db.query(models.Membership)
        .filter(
            models.Membership.workspace_id == invite.workspace_id,
            models.Membership.user_id == current_user.user_id,
        )
        .first()
    )
    if not membership:
        membership = models.Membership(
            workspace_id=invite.workspace_id,
            user_id=current_user.user_id,
            role="athlete",
            status="active",
        )
        db.add(membership)
    elif membership.status != "active":
        membership.status = "active"
    db.commit()
    db.refresh(membership)
    return membership


@router.put("/profile", response_model=schemas.AthleteProfileUpdateResponse)
def update_profile(
    data: schemas.AthleteProfileUpdate,
    current_user: models.User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    current_user.name = data.name
    current_user.preferred_name = data.preferred_name

    profile = (
        db.query(models.AthleteProfile)
        .filter(models.AthleteProfile.user_id == current_user.user_id)
        .first()
    )
    if not profile:
        profile = models.AthleteProfile(user_id=current_user.user_id)
        db.add(profile)
        db.flush()

    for field, value in data.model_dump(exclude={"name", "preferred_name"}).items():
        setattr(profile, field, value)

    whatsapp_identity = None
    if data.whatsapp_phone:
        whatsapp_identity = (
            db.query(models.WhatsAppIdentity)
            .filter(models.WhatsAppIdentity.user_id == current_user.user_id)
            .first()
        )
        if not whatsapp_identity:
            whatsapp_identity = models.WhatsAppIdentity(
                user_id=current_user.user_id,
                phone=data.whatsapp_phone,
            )
            db.add(whatsapp_identity)
        else:
            whatsapp_identity.phone = data.whatsapp_phone

    db.commit()
    db.refresh(current_user)
    db.refresh(profile)
    if whatsapp_identity:
        db.refresh(whatsapp_identity)
    return {
        "user": current_user,
        "profile": profile,
        "whatsapp_identity": whatsapp_identity,
    }
