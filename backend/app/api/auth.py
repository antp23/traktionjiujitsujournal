"""Passwordless auth: request a magic link, consume it, manage the session."""
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session as DBSession

from app import config, models, schemas, security
from app.api.deps import get_current_user
from app.db import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/request-link", response_model=schemas.AuthLinkResponse)
def request_link(data: schemas.AuthLinkRequest, db: DBSession = Depends(get_db)):
    email = security.normalize_email(data.email)
    dev_tokens_enabled = config.dev_auth_tokens_enabled()
    if not dev_tokens_enabled and not security.email_delivery_available():
        raise HTTPException(status_code=503, detail="Email login is not configured")

    security.enforce_request_throttle(db, email)

    token = models.AuthToken(
        email=email,
        token_type="magic_link",
        expires_at=security.magic_link_expires_at(),
    )
    db.add(token)
    db.commit()
    db.refresh(token)

    if security.email_delivery_available():
        try:
            security.send_magic_link_email(email, token.token)
        except Exception as exc:
            raise HTTPException(status_code=502, detail="Could not send sign-in email") from exc

    return {
        "message": security.SAFE_LINK_MESSAGE,
        "dev_token": token.token if dev_tokens_enabled else None,
    }


@router.post("/consume-link", response_model=schemas.AuthConsumeResponse)
def consume_link(data: schemas.AuthConsumeRequest, db: DBSession = Depends(get_db)):
    auth_token = (
        db.query(models.AuthToken)
        .filter(
            models.AuthToken.token == data.token,
            models.AuthToken.token_type == "magic_link",
            models.AuthToken.consumed_at.is_(None),
        )
        .first()
    )
    if not auth_token:
        raise HTTPException(status_code=400, detail="Invalid or consumed token")
    if auth_token.expires_at <= security.now():
        raise HTTPException(status_code=400, detail="Expired token")

    user = db.query(models.User).filter(models.User.email == auth_token.email).first()
    if not user:
        user = models.User(email=auth_token.email)
        db.add(user)
        db.flush()

    auth_token.user_id = user.user_id
    auth_token.consumed_at = security.now()
    session = models.AuthToken(
        email=user.email,
        user_id=user.user_id,
        token_type="session",
        expires_at=security.session_expires_at(),
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    db.refresh(user)
    return {"session_token": session.token, "user": user}


@router.post("/logout")
def logout(
    x_session_token: str = Header(default=None),
    db: DBSession = Depends(get_db),
):
    token = security.resolve_session(db, x_session_token)
    token.consumed_at = security.now()
    db.commit()
    return {"message": "Logged out."}


@router.get("/me", response_model=schemas.AuthMeResponse)
def me(
    current_user: models.User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    memberships = (
        db.query(models.Membership)
        .filter(models.Membership.user_id == current_user.user_id)
        .all()
    )
    profile = (
        db.query(models.AthleteProfile)
        .filter(models.AthleteProfile.user_id == current_user.user_id)
        .first()
    )
    return {"user": current_user, "memberships": memberships, "profile": profile}
