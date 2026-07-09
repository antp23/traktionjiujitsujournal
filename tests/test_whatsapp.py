"""Characterization: Meta WhatsApp webhook (feature-flagged capture)."""
import hashlib
import hmac
import json
import os

import models

VERIFY_PARAMS = {
    "hub.mode": "subscribe",
    "hub.verify_token": "verify-me",
    "hub.challenge": "challenge-123",
}


def _enable():
    os.environ["BJJ_ENABLE_WHATSAPP_CAPTURE"] = "true"
    os.environ["BJJ_META_VERIFY_TOKEN"] = "verify-me"
    os.environ["BJJ_META_APP_SECRET"] = "app-secret"


def _payload(message_id="wamid.1", from_phone="15555555555",
             body="note: manage the gas tank", message_type="text"):
    message = {"id": message_id, "from": from_phone, "timestamp": "1770000000",
               "type": message_type}
    if message_type == "text":
        message["text"] = {"body": body}
    return {
        "object": "whatsapp_business_account",
        "entry": [{"changes": [{"field": "messages", "value": {
            "metadata": {"phone_number_id": "12345"},
            "messages": [message],
        }}]}],
    }


def _post(client, payload):
    raw = json.dumps(payload, separators=(",", ":")).encode()
    signature = hmac.new(b"app-secret", raw, hashlib.sha256).hexdigest()
    return client.post(
        "/webhooks/whatsapp/meta",
        content=raw,
        headers={"content-type": "application/json",
                 "x-hub-signature-256": f"sha256={signature}"},
    )


def _register_phone(client, auth_headers, phone="+15555555555"):
    headers = auth_headers("athlete@example.com")
    response = client.put("/workspaces/profile", headers=headers,
                          json={"name": "Athlete", "whatsapp_phone": phone})
    assert response.status_code == 200
    return headers


class TestFeatureFlag:
    def test_disabled_by_default(self, client):
        assert client.get("/webhooks/whatsapp/meta", params=VERIFY_PARAMS).status_code == 404
        assert client.post("/webhooks/whatsapp/meta", json={}).status_code == 404


class TestVerification:
    def test_challenge_echo(self, client):
        _enable()
        response = client.get("/webhooks/whatsapp/meta", params=VERIFY_PARAMS)
        assert response.status_code == 200
        assert response.text == "challenge-123"

    def test_wrong_verify_token(self, client):
        _enable()
        response = client.get("/webhooks/whatsapp/meta",
                              params={**VERIFY_PARAMS, "hub.verify_token": "wrong"})
        assert response.status_code == 403

    def test_bad_signature_rejected(self, client):
        _enable()
        response = client.post("/webhooks/whatsapp/meta", json={"entry": []},
                               headers={"x-hub-signature-256": "sha256=bad"})
        assert response.status_code == 401

    def test_missing_signature_rejected(self, client):
        _enable()
        assert client.post("/webhooks/whatsapp/meta", json={"entry": []}).status_code == 401


class TestCapture:
    def test_matched_message_is_parsed_into_private_note(self, client, auth_headers, db):
        _enable()
        _register_phone(client, auth_headers)

        response = _post(client, _payload())
        assert response.status_code == 200
        assert response.json() == {"ok": True, "processed": 1, "duplicates": 0, "unmatched": 0}

        user = db.query(models.User).filter(models.User.email == "athlete@example.com").one()
        inbound = db.query(models.InboundMessage).one()
        assert inbound.provider == "meta"
        assert inbound.provider_message_id == "wamid.1"
        assert inbound.from_phone == "+15555555555"
        assert inbound.owner_user_id == user.user_id
        assert inbound.parsed_status == "parsed"
        assert inbound.parse_action == "note_logged"

        note = db.query(models.Note).one()
        assert note.owner_user_id == user.user_id
        assert "manage the gas tank" in note.content

    def test_duplicate_message_ids_are_ignored(self, client, auth_headers, db):
        _enable()
        _register_phone(client, auth_headers)
        assert _post(client, _payload()).json()["processed"] == 1
        assert _post(client, _payload()).json() == {
            "ok": True, "processed": 0, "duplicates": 1, "unmatched": 0,
        }
        assert db.query(models.InboundMessage).count() == 1
        assert db.query(models.Note).count() == 1

    def test_unknown_phone_is_stored_unmatched(self, client, db):
        _enable()
        response = _post(client, _payload(from_phone="19999999999"))
        assert response.json() == {"ok": True, "processed": 0, "duplicates": 0, "unmatched": 1}
        inbound = db.query(models.InboundMessage).one()
        assert inbound.owner_user_id is None
        assert inbound.parsed_status == "unmatched"
        assert db.query(models.Note).count() == 0

    def test_non_text_messages_are_skipped(self, client, auth_headers, db):
        _enable()
        _register_phone(client, auth_headers)
        response = _post(client, _payload(message_type="image"))
        assert response.json() == {"ok": True, "processed": 0, "duplicates": 0, "unmatched": 0}
        assert db.query(models.InboundMessage).count() == 0
