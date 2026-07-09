"""Meta WhatsApp webhook (feature-flagged capture into the private journal)."""
import hashlib
import hmac
import json
import re
from datetime import datetime
from typing import Any, Iterator, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session as DBSession

from app import config, models
from app.db import get_db
from app.services.quicklog import parse_text_to_private_journal

router = APIRouter(prefix="/webhooks/whatsapp", tags=["whatsapp"])


def _require_capture_enabled() -> None:
    if not config.whatsapp_capture_enabled():
        raise HTTPException(status_code=404, detail="WhatsApp capture is disabled")


def _normalize_phone(phone: Optional[str]) -> str:
    if not phone:
        return ""
    digits = re.sub(r"\D+", "", phone)
    return f"+{digits}" if digits else ""


def _verify_meta_signature(raw_body: bytes, signature_header: Optional[str]) -> None:
    app_secret = config.meta_app_secret()
    if not app_secret:
        raise HTTPException(status_code=500, detail="Meta app secret is not configured")
    if not signature_header or not signature_header.startswith("sha256="):
        raise HTTPException(status_code=401, detail="Missing Meta signature")

    expected = hmac.new(app_secret.encode(), raw_body, hashlib.sha256).hexdigest()
    supplied = signature_header.removeprefix("sha256=")
    if not hmac.compare_digest(expected, supplied):
        raise HTTPException(status_code=401, detail="Invalid Meta signature")


def _iter_text_messages(payload: dict[str, Any]) -> Iterator[dict[str, Any]]:
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            metadata = value.get("metadata", {})
            to_phone = metadata.get("display_phone_number") or metadata.get("phone_number_id")
            for message in value.get("messages", []):
                if message.get("type") != "text":
                    continue
                message_id = message.get("id")
                from_phone = message.get("from")
                body = (message.get("text") or {}).get("body")
                if message_id and from_phone and body:
                    yield {
                        "provider_message_id": message_id,
                        "from_phone": _normalize_phone(from_phone),
                        "to_phone": to_phone,
                        "body": body,
                    }


@router.get("/meta", response_class=PlainTextResponse)
def verify_meta_webhook(
    mode: Optional[str] = Query(default=None, alias="hub.mode"),
    verify_token: Optional[str] = Query(default=None, alias="hub.verify_token"),
    challenge: Optional[str] = Query(default=None, alias="hub.challenge"),
):
    _require_capture_enabled()
    configured_token = config.meta_verify_token()
    if (
        mode == "subscribe"
        and configured_token
        and hmac.compare_digest(verify_token or "", configured_token)
    ):
        return challenge or ""
    raise HTTPException(status_code=403, detail="Invalid webhook verification token")


@router.post("/meta")
async def receive_meta_webhook(request: Request, db: DBSession = Depends(get_db)):
    _require_capture_enabled()
    raw_body = await request.body()
    _verify_meta_signature(raw_body, request.headers.get("x-hub-signature-256"))

    try:
        payload = json.loads(raw_body.decode() or "{}")
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from exc

    processed = duplicates = unmatched = 0

    for incoming in _iter_text_messages(payload):
        already_seen = (
            db.query(models.InboundMessage)
            .filter(
                models.InboundMessage.provider == "meta",
                models.InboundMessage.provider_message_id == incoming["provider_message_id"],
            )
            .first()
        )
        if already_seen:
            duplicates += 1
            continue

        identity = (
            db.query(models.WhatsAppIdentity)
            .filter(models.WhatsAppIdentity.phone == incoming["from_phone"])
            .first()
        )
        owner_user_id = identity.user_id if identity else None
        inbound = models.InboundMessage(
            provider="meta",
            provider_message_id=incoming["provider_message_id"],
            from_phone=incoming["from_phone"],
            to_phone=incoming["to_phone"],
            owner_user_id=owner_user_id,
            raw_body=incoming["body"],
            parsed_status="unmatched" if owner_user_id is None else "received",
            received_at=datetime.utcnow(),
        )
        db.add(inbound)
        db.flush()

        if owner_user_id is None:
            unmatched += 1
            continue

        parse_result = parse_text_to_private_journal(incoming["body"], owner_user_id, db)
        inbound.parsed_status = "parsed" if parse_result.success else "parse_failed"
        inbound.parse_action = parse_result.action
        inbound.parse_message = parse_result.message
        processed += 1

    db.commit()
    return {
        "ok": True,
        "processed": processed,
        "duplicates": duplicates,
        "unmatched": unmatched,
    }
