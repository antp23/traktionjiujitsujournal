"""Authentication primitives: magic links, session tokens, throttling,
and sign-in email delivery."""
import hashlib
import secrets
import smtplib
from datetime import datetime, timedelta
from email.message import EmailMessage
from urllib.parse import urlencode

from fastapi import HTTPException
from sqlalchemy.orm import Session as DBSession

from app import config, models

SAFE_LINK_MESSAGE = "If the email is allowed, a sign-in link will be sent."


def normalize_email(email: str) -> str:
    return email.strip().lower()


def now() -> datetime:
    return datetime.utcnow()


def magic_link_expires_at() -> datetime:
    return now() + timedelta(minutes=config.magic_link_ttl_minutes())


def session_expires_at() -> datetime:
    return now() + timedelta(hours=config.session_ttl_hours())


def email_delivery_available() -> bool:
    return config.smtp_configured()


def magic_login_url(token: str) -> str:
    return f"{config.frontend_url()}/login?{urlencode({'token': token})}"


def send_magic_link_email(email: str, token: str) -> None:
    """Deliver a sign-in link over SMTP. Raises on any delivery problem."""
    if not email_delivery_available():
        raise RuntimeError("Email delivery is not configured")

    message = EmailMessage()
    message["Subject"] = "Sign in to BJJ Tracker"
    message["From"] = config.env_str("BJJ_EMAIL_FROM")
    message["To"] = email
    message.set_content(
        "\n".join(
            [
                "Sign in to BJJ Tracker:",
                "",
                magic_login_url(token),
                "",
                "This link expires soon. If you did not request it, you can ignore this email.",
            ]
        )
    )

    host = config.env_str("BJJ_SMTP_HOST")
    use_ssl = config.env_bool("BJJ_SMTP_USE_SSL", True)
    use_tls = config.env_bool("BJJ_SMTP_USE_TLS", not use_ssl)
    port = config.env_int("BJJ_SMTP_PORT", 465 if use_ssl else 587)
    username = config.env_str("BJJ_SMTP_USERNAME")
    password = config.env_str("BJJ_SMTP_PASSWORD")

    smtp_class = smtplib.SMTP_SSL if use_ssl else smtplib.SMTP
    with smtp_class(host, port, timeout=10) as smtp:
        if use_tls and not use_ssl:
            smtp.starttls()
        if username and password:
            smtp.login(username, password)
        smtp.send_message(message)


def enforce_request_throttle(db: DBSession, email: str) -> None:
    """Reject the request with 429 once an email exceeds its link budget."""
    cutoff = now() - timedelta(minutes=config.auth_request_window_minutes())
    recent = (
        db.query(models.AuthToken)
        .filter(
            models.AuthToken.email == email,
            models.AuthToken.token_type == "magic_link",
            models.AuthToken.created_at >= cutoff,
        )
        .count()
    )
    if recent >= config.auth_request_limit():
        raise HTTPException(
            status_code=429,
            detail="Too many sign-in link requests. Try again later.",
        )


def resolve_session(db: DBSession, session_token: str | None) -> models.AuthToken:
    """Validate a session token and return its AuthToken row (with user)."""
    if not session_token:
        raise HTTPException(status_code=401, detail="Missing session token")
    token = (
        db.query(models.AuthToken)
        .filter(
            models.AuthToken.token == session_token,
            models.AuthToken.token_type == "session",
        )
        .first()
    )
    if not token or not token.user:
        raise HTTPException(status_code=401, detail="Invalid session token")
    if token.consumed_at is not None:
        raise HTTPException(status_code=401, detail="Revoked session token")
    if token.expires_at <= now():
        raise HTTPException(status_code=401, detail="Expired session token")
    return token


API_KEY_PREFIX = "bjj_"


def generate_api_key() -> str:
    return API_KEY_PREFIX + secrets.token_urlsafe(32)


def hash_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def resolve_api_key(db: DBSession, raw_key: str) -> models.ApiKey:
    """Validate a personal API key and stamp last_used_at."""
    key = (
        db.query(models.ApiKey)
        .filter(models.ApiKey.key_hash == hash_api_key(raw_key))
        .first()
    )
    if not key or key.revoked_at is not None or not key.user:
        raise HTTPException(status_code=401, detail="Invalid API key")
    key.last_used_at = now()
    db.commit()
    return key


def bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    scheme, _, value = authorization.partition(" ")
    if scheme.lower() != "bearer" or not value.strip():
        return None
    return value.strip()


def resolve_user(
    db: DBSession, session_token: str | None, authorization: str | None
) -> models.User:
    """Resolve the caller from a session token or a personal API key.

    API keys are accepted as `Authorization: Bearer bjj_...` or in the
    X-Session-Token header."""
    bearer = bearer_token(authorization)
    if bearer and bearer.startswith(API_KEY_PREFIX):
        return resolve_api_key(db, bearer).user
    if session_token and session_token.startswith(API_KEY_PREFIX):
        return resolve_api_key(db, session_token).user
    return resolve_session(db, session_token or bearer).user
