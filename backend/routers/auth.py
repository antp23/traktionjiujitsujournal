import os
import smtplib
from datetime import datetime, timedelta
from email.message import EmailMessage
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session as DBSession

import models
import schemas
from database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])

DEFAULT_MAGIC_LINK_TTL_MINUTES = 15
DEFAULT_SESSION_TTL_HOURS = 24 * 30
DEFAULT_REQUEST_LIMIT = 5
DEFAULT_REQUEST_WINDOW_MINUTES = 15
SAFE_LINK_MESSAGE = "If the email is allowed, a sign-in link will be sent."


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _now() -> datetime:
    return datetime.utcnow()


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _public_frontend_url() -> str:
    return os.getenv("BJJ_FRONTEND_URL", "http://localhost:5173").rstrip("/")


def _smtp_configured() -> bool:
    return bool(
        os.getenv("BJJ_SMTP_HOST")
        and os.getenv("BJJ_EMAIL_FROM")
    )


def _magic_login_url(token: str) -> str:
    return f"{_public_frontend_url()}/login?{urlencode({'token': token})}"


def _send_magic_link_email(email: str, token: str) -> None:
    if not _smtp_configured():
        return

    link = _magic_login_url(token)
    message = EmailMessage()
    message["Subject"] = "Sign in to BJJ Tracker"
    message["From"] = os.getenv("BJJ_EMAIL_FROM")
    message["To"] = email
    message.set_content(
        "\n".join(
            [
                "Sign in to BJJ Tracker:",
                "",
                link,
                "",
                "This link expires soon. If you did not request it, you can ignore this email.",
            ]
        )
    )

    host = os.getenv("BJJ_SMTP_HOST")
    port = _env_int("BJJ_SMTP_PORT", 465 if _env_bool("BJJ_SMTP_USE_SSL", True) else 587)
    username = os.getenv("BJJ_SMTP_USERNAME")
    password = os.getenv("BJJ_SMTP_PASSWORD")
    use_ssl = _env_bool("BJJ_SMTP_USE_SSL", True)
    use_tls = _env_bool("BJJ_SMTP_USE_TLS", not use_ssl)

    smtp_class = smtplib.SMTP_SSL if use_ssl else smtplib.SMTP
    with smtp_class(host, port, timeout=10) as smtp:
        if use_tls and not use_ssl:
            smtp.starttls()
        if username and password:
            smtp.login(username, password)
        smtp.send_message(message)


def _magic_link_expires_at() -> datetime:
    minutes = max(1, _env_int("BJJ_AUTH_MAGIC_LINK_TTL_MINUTES", DEFAULT_MAGIC_LINK_TTL_MINUTES))
    return _now() + timedelta(minutes=minutes)


def _session_expires_at() -> datetime:
    hours = max(1, _env_int("BJJ_AUTH_SESSION_TTL_HOURS", DEFAULT_SESSION_TTL_HOURS))
    return _now() + timedelta(hours=hours)


def _current_session(
    x_session_token: str,
    db: DBSession,
) -> models.AuthToken:
    if not x_session_token:
        raise HTTPException(status_code=401, detail="Missing session token")
    token = (
        db.query(models.AuthToken)
        .filter(
            models.AuthToken.token == x_session_token,
            models.AuthToken.token_type == "session",
        )
        .first()
    )
    if not token or not token.user:
        raise HTTPException(status_code=401, detail="Invalid session token")
    if token.consumed_at is not None:
        raise HTTPException(status_code=401, detail="Revoked session token")
    if token.expires_at <= _now():
        raise HTTPException(status_code=401, detail="Expired session token")
    return token


def get_current_user(
    x_session_token: str = Header(default=None),
    db: DBSession = Depends(get_db),
):
    token = _current_session(x_session_token, db)
    return token.user


@router.post("/request-link", response_model=schemas.AuthLinkResponse)
def request_link(data: schemas.AuthLinkRequest, db: DBSession = Depends(get_db)):
    email = _normalize_email(data.email)
    request_window_minutes = max(
        1,
        _env_int("BJJ_AUTH_REQUEST_WINDOW_MINUTES", DEFAULT_REQUEST_WINDOW_MINUTES),
    )
    request_limit = max(1, _env_int("BJJ_AUTH_REQUEST_LIMIT", DEFAULT_REQUEST_LIMIT))
    cutoff = _now() - timedelta(minutes=request_window_minutes)
    recent_request_count = (
        db.query(models.AuthToken)
        .filter(
            models.AuthToken.email == email,
            models.AuthToken.token_type == "magic_link",
            models.AuthToken.created_at >= cutoff,
        )
        .count()
    )
    if recent_request_count >= request_limit:
        raise HTTPException(
            status_code=429,
            detail="Too many sign-in link requests. Try again later.",
        )

    token = models.AuthToken(
        email=email,
        token_type="magic_link",
        expires_at=_magic_link_expires_at(),
    )
    db.add(token)
    db.commit()
    db.refresh(token)
    try:
        _send_magic_link_email(email, token.token)
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Could not send sign-in email") from exc
    return {
        "message": SAFE_LINK_MESSAGE,
        "dev_token": token.token if _env_bool("BJJ_DEV_AUTH_TOKENS") else None,
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
    if auth_token.expires_at <= _now():
        raise HTTPException(status_code=400, detail="Expired token")

    user = db.query(models.User).filter(models.User.email == auth_token.email).first()
    if not user:
        user = models.User(email=auth_token.email)
        db.add(user)
        db.flush()

    auth_token.user_id = user.user_id
    auth_token.consumed_at = _now()
    session = models.AuthToken(
        email=user.email,
        user_id=user.user_id,
        token_type="session",
        expires_at=_session_expires_at(),
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
    token = _current_session(x_session_token, db)
    token.consumed_at = _now()
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
