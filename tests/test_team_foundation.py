import pathlib
import sys
import unittest
import hashlib
import hmac
import json
import os
from datetime import date, datetime, timedelta
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

import database  # noqa: E402
import main  # noqa: E402
import models  # noqa: E402


class TeamFoundationTests(unittest.TestCase):
    def setUp(self):
        self._original_env = {
            "BJJ_DEV_AUTH_TOKENS": os.environ.get("BJJ_DEV_AUTH_TOKENS"),
            "BJJ_AUTH_REQUEST_LIMIT": os.environ.get("BJJ_AUTH_REQUEST_LIMIT"),
            "BJJ_AUTH_REQUEST_WINDOW_MINUTES": os.environ.get("BJJ_AUTH_REQUEST_WINDOW_MINUTES"),
            "BJJ_FRONTEND_URL": os.environ.get("BJJ_FRONTEND_URL"),
            "BJJ_EMAIL_FROM": os.environ.get("BJJ_EMAIL_FROM"),
            "BJJ_SMTP_HOST": os.environ.get("BJJ_SMTP_HOST"),
            "BJJ_SMTP_PORT": os.environ.get("BJJ_SMTP_PORT"),
            "BJJ_SMTP_USERNAME": os.environ.get("BJJ_SMTP_USERNAME"),
            "BJJ_SMTP_PASSWORD": os.environ.get("BJJ_SMTP_PASSWORD"),
            "BJJ_SMTP_USE_TLS": os.environ.get("BJJ_SMTP_USE_TLS"),
            "BJJ_SMTP_USE_SSL": os.environ.get("BJJ_SMTP_USE_SSL"),
        }
        os.environ.pop("BJJ_DEV_AUTH_TOKENS", None)
        os.environ.pop("BJJ_AUTH_REQUEST_LIMIT", None)
        os.environ.pop("BJJ_AUTH_REQUEST_WINDOW_MINUTES", None)
        os.environ.pop("BJJ_FRONTEND_URL", None)
        os.environ.pop("BJJ_EMAIL_FROM", None)
        os.environ.pop("BJJ_SMTP_HOST", None)
        os.environ.pop("BJJ_SMTP_PORT", None)
        os.environ.pop("BJJ_SMTP_USERNAME", None)
        os.environ.pop("BJJ_SMTP_PASSWORD", None)
        os.environ.pop("BJJ_SMTP_USE_TLS", None)
        os.environ.pop("BJJ_SMTP_USE_SSL", None)

        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        self.SessionTesting = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
        )
        database.Base.metadata.create_all(bind=self.engine)

        def override_get_db():
            db = self.SessionTesting()
            try:
                yield db
            finally:
                db.close()

        main.app.dependency_overrides[database.get_db] = override_get_db
        self.client = TestClient(main.app)

    def tearDown(self):
        main.app.dependency_overrides.clear()
        database.Base.metadata.drop_all(bind=self.engine)
        for key, value in self._original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def test_team_tables_are_created(self):
        table_names = set(inspect(self.engine).get_table_names())

        self.assertTrue(
            {
                "users",
                "auth_tokens",
                "gym_workspaces",
                "memberships",
                "invite_links",
                "athlete_profiles",
                "whatsapp_identities",
                "goals",
                "share_threads",
                "thread_messages",
                "coach_notes",
                "inbound_messages",
            }.issubset(table_names)
        )

    def test_auth_workspace_join_and_profile_flow(self):
        dev_token = self._magic_link_for_email("athlete@example.com")
        session_response = self.client.post(
            "/auth/consume-link",
            json={"token": dev_token},
        )
        self.assertEqual(session_response.status_code, 200)
        session_token = session_response.json()["session_token"]

        me_response = self.client.get(
            "/auth/me",
            headers={"x-session-token": session_token},
        )
        self.assertEqual(me_response.status_code, 200)
        self.assertEqual(me_response.json()["user"]["email"], "athlete@example.com")
        self.assertEqual(me_response.json()["memberships"], [])
        self.assertIsNone(me_response.json()["profile"])

        bootstrap_response = self.client.post(
            "/workspaces/bootstrap",
            json={
                "gym_name": "Traktion Jiujitsu Academy",
                "owner_email": "owner@example.com",
                "owner_name": "Anthony",
            },
        )
        self.assertEqual(bootstrap_response.status_code, 200)
        invite_code = bootstrap_response.json()["invite"]["code"]

        invite_response = self.client.get(f"/workspaces/invites/{invite_code}")
        self.assertEqual(invite_response.status_code, 200)
        self.assertEqual(invite_response.json()["gym_name"], "Traktion Jiujitsu Academy")
        self.assertTrue(invite_response.json()["usable"])

        join_response = self.client.post(
            "/workspaces/join",
            headers={"x-session-token": session_token},
            json={"invite_code": invite_code},
        )
        self.assertEqual(join_response.status_code, 200)
        self.assertEqual(join_response.json()["role"], "athlete")

        current_workspace = self.client.get(
            "/workspaces/current",
            headers={"x-session-token": session_token},
        )
        self.assertEqual(current_workspace.status_code, 200)
        self.assertEqual(current_workspace.json()["workspace"]["gym_name"], "Traktion Jiujitsu Academy")
        self.assertEqual(current_workspace.json()["membership"]["role"], "athlete")
        self.assertIsNone(current_workspace.json()["invite"])

        profile_response = self.client.put(
            "/workspaces/profile",
            headers={"x-session-token": session_token},
            json={
                "name": "Student Name",
                "preferred_name": "Student",
                "whatsapp_phone": "+15555555555",
                "belt": "blue",
                "stripes": 1,
                "years_training": 2,
                "typical_training_frequency": "3x/week",
                "gi_nogi_preference": "both",
                "competition_interest": "maybe",
                "current_focus": "guard retention",
                "favorite_positions": ["De La Riva"],
                "problem_positions": ["bottom half"],
                "injuries_or_limitations": "left shoulder",
            },
        )
        self.assertEqual(profile_response.status_code, 200)
        payload = profile_response.json()
        self.assertEqual(payload["user"]["name"], "Student Name")
        self.assertEqual(payload["profile"]["belt"], "blue")
        self.assertEqual(payload["whatsapp_identity"]["phone"], "+15555555555")

    def test_private_goals_and_explicit_goal_sharing(self):
        owner_session = self._session_for_email("owner@example.com")
        athlete_session = self._session_for_email("athlete@example.com")
        other_session = self._session_for_email("other@example.com")
        invite_code = self._bootstrap_workspace()

        self.client.post(
            "/workspaces/join",
            headers={"x-session-token": athlete_session},
            json={"invite_code": invite_code},
        )
        self.client.post(
            "/workspaces/join",
            headers={"x-session-token": other_session},
            json={"invite_code": invite_code},
        )

        goal_response = self.client.post(
            "/goals",
            headers={"x-session-token": athlete_session},
            json={
                "title": "Fix collar choke defense",
                "description": "Stop getting folded in top half.",
                "target_date": str(date.today()),
            },
        )
        self.assertEqual(goal_response.status_code, 201)
        goal = goal_response.json()
        self.assertEqual(goal["visibility"], "private")

        other_goals = self.client.get(
            "/goals",
            headers={"x-session-token": other_session},
        )
        self.assertEqual(other_goals.status_code, 200)
        self.assertEqual(other_goals.json(), [])

        thread_response = self.client.post(
            "/sharing/threads",
            headers={"x-session-token": athlete_session},
            json={
                "source_type": "goal",
                "source_id": goal["goal_id"],
                "body": "Can you look at this?",
            },
        )
        self.assertEqual(thread_response.status_code, 201)
        thread = thread_response.json()["thread"]

        athlete_inbox = self.client.get(
            "/sharing/inbox",
            headers={"x-session-token": athlete_session},
        )
        self.assertEqual(len(athlete_inbox.json()), 1)

        owner_inbox = self.client.get(
            "/sharing/inbox",
            headers={"x-session-token": owner_session},
        )
        self.assertEqual(owner_inbox.status_code, 200)
        self.assertEqual(owner_inbox.json()[0]["thread_id"], thread["thread_id"])

        reply_response = self.client.post(
            f"/sharing/threads/{thread['thread_id']}/messages",
            headers={"x-session-token": owner_session},
            json={"body": "Frame first, then recover knee line."},
        )
        self.assertEqual(reply_response.status_code, 201)
        message_id = reply_response.json()["message_id"]

        pin_response = self.client.post(
            f"/sharing/messages/{message_id}/pin",
            headers={"x-session-token": owner_session},
        )
        self.assertEqual(pin_response.status_code, 201)
        self.assertEqual(pin_response.json()["content"], "Frame first, then recover knee line.")
        self.assertEqual(pin_response.json()["source"], "coach")

    def test_magic_link_cannot_be_consumed_twice(self):
        token = self._magic_link_for_email("athlete@example.com")

        first_response = self.client.post("/auth/consume-link", json={"token": token})
        self.assertEqual(first_response.status_code, 200)

        second_response = self.client.post("/auth/consume-link", json={"token": token})
        self.assertEqual(second_response.status_code, 400)

    def test_expired_magic_link_is_rejected(self):
        token = self._magic_link_for_email("athlete@example.com")
        db = self.SessionTesting()
        try:
            auth_token = db.query(models.AuthToken).filter(models.AuthToken.token == token).one()
            auth_token.expires_at = datetime.utcnow() - timedelta(minutes=1)
            db.commit()
        finally:
            db.close()

        response = self.client.post("/auth/consume-link", json={"token": token})

        self.assertEqual(response.status_code, 400)
        self.assertIn("expired", response.json()["detail"].lower())

    def test_expired_session_is_rejected(self):
        session_token = self._session_for_email("athlete@example.com")
        db = self.SessionTesting()
        try:
            auth_token = db.query(models.AuthToken).filter(models.AuthToken.token == session_token).one()
            auth_token.expires_at = datetime.utcnow() - timedelta(minutes=1)
            db.commit()
        finally:
            db.close()

        response = self.client.get(
            "/auth/me",
            headers={"x-session-token": session_token},
        )

        self.assertEqual(response.status_code, 401)
        self.assertIn("expired", response.json()["detail"].lower())

    def test_logout_revokes_session(self):
        session_token = self._session_for_email("athlete@example.com")

        logout_response = self.client.post(
            "/auth/logout",
            headers={"x-session-token": session_token},
        )
        self.assertEqual(logout_response.status_code, 200)

        me_response = self.client.get(
            "/auth/me",
            headers={"x-session-token": session_token},
        )
        self.assertEqual(me_response.status_code, 401)

    def test_dev_token_is_hidden_unless_enabled(self):
        response = self.client.post(
            "/auth/request-link",
            json={"email": "athlete@example.com"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json()["dev_token"])

        os.environ["BJJ_DEV_AUTH_TOKENS"] = "true"
        dev_response = self.client.post(
            "/auth/request-link",
            json={"email": "other@example.com"},
        )

        self.assertEqual(dev_response.status_code, 200)
        self.assertIsInstance(dev_response.json()["dev_token"], str)

    def test_request_link_sends_email_when_smtp_is_configured(self):
        os.environ["BJJ_FRONTEND_URL"] = "https://bjj.example.com"
        os.environ["BJJ_EMAIL_FROM"] = "BJJ Tracker <no-reply@bjj.example.com>"
        os.environ["BJJ_SMTP_HOST"] = "smtp.example.com"
        os.environ["BJJ_SMTP_PORT"] = "465"
        os.environ["BJJ_SMTP_USERNAME"] = "smtp-user"
        os.environ["BJJ_SMTP_PASSWORD"] = "smtp-pass"
        os.environ["BJJ_SMTP_USE_SSL"] = "true"

        with patch("routers.auth.smtplib.SMTP_SSL") as smtp_ssl:
            response = self.client.post(
                "/auth/request-link",
                json={"email": "athlete@example.com"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json()["dev_token"])
        smtp_ssl.assert_called_once_with("smtp.example.com", 465, timeout=10)
        smtp = smtp_ssl.return_value.__enter__.return_value
        smtp.login.assert_called_once_with("smtp-user", "smtp-pass")
        self.assertEqual(smtp.send_message.call_count, 1)
        message = smtp.send_message.call_args.args[0]
        self.assertEqual(message["To"], "athlete@example.com")
        self.assertEqual(message["From"], "BJJ Tracker <no-reply@bjj.example.com>")
        self.assertIn("Sign in to BJJ Tracker", message["Subject"])
        body = message.get_body(preferencelist=("plain",)).get_content()
        self.assertIn("https://bjj.example.com/login?token=", body)
        self.assertNotIn("None", body)

    def test_magic_link_requests_are_throttled_per_email(self):
        os.environ["BJJ_AUTH_REQUEST_LIMIT"] = "2"
        os.environ["BJJ_DEV_AUTH_TOKENS"] = "true"

        self.assertEqual(
            self.client.post("/auth/request-link", json={"email": "athlete@example.com"}).status_code,
            200,
        )
        self.assertEqual(
            self.client.post("/auth/request-link", json={"email": "ATHLETE@example.com"}).status_code,
            200,
        )
        throttled_response = self.client.post(
            "/auth/request-link",
            json={"email": "athlete@example.com"},
        )

        self.assertEqual(throttled_response.status_code, 429)

    def test_meta_whatsapp_webhook_verifies_challenge_and_logs_private_note(self):
        os.environ["BJJ_ENABLE_WHATSAPP_CAPTURE"] = "true"
        os.environ["BJJ_META_VERIFY_TOKEN"] = "verify-me"
        os.environ["BJJ_META_APP_SECRET"] = "app-secret"
        session_token = self._session_for_email("athlete@example.com")

        self._bootstrap_workspace()
        profile_response = self.client.put(
            "/workspaces/profile",
            headers={"x-session-token": session_token},
            json={
                "name": "Athlete",
                "preferred_name": "Athlete",
                "whatsapp_phone": "+15555555555",
            },
        )
        self.assertEqual(profile_response.status_code, 200)

        verify_response = self.client.get(
            "/webhooks/whatsapp/meta",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "verify-me",
                "hub.challenge": "challenge-123",
            },
        )
        self.assertEqual(verify_response.status_code, 200)
        self.assertEqual(verify_response.text, "challenge-123")

        payload = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "changes": [
                        {
                            "field": "messages",
                            "value": {
                                "metadata": {"phone_number_id": "12345"},
                                "messages": [
                                    {
                                        "id": "wamid.private-note-1",
                                        "from": "15555555555",
                                        "timestamp": "1770000000",
                                        "type": "text",
                                        "text": {
                                            "body": "note: Coach said manage my gas tank before attacking."
                                        },
                                    }
                                ],
                            },
                        }
                    ]
                }
            ],
        }
        raw_body = json.dumps(payload, separators=(",", ":")).encode()
        signature = hmac.new(b"app-secret", raw_body, hashlib.sha256).hexdigest()

        webhook_response = self.client.post(
            "/webhooks/whatsapp/meta",
            content=raw_body,
            headers={
                "content-type": "application/json",
                "x-hub-signature-256": f"sha256={signature}",
            },
        )
        self.assertEqual(webhook_response.status_code, 200)
        self.assertEqual(webhook_response.json()["processed"], 1)

        db = self.SessionTesting()
        try:
            user = db.query(models.User).filter(models.User.email == "athlete@example.com").one()
            inbound = db.query(models.InboundMessage).one()
            note = db.query(models.Note).one()

            self.assertEqual(inbound.owner_user_id, user.user_id)
            self.assertEqual(inbound.provider, "meta")
            self.assertEqual(inbound.provider_message_id, "wamid.private-note-1")
            self.assertEqual(inbound.parsed_status, "parsed")
            self.assertEqual(note.owner_user_id, user.user_id)
            self.assertIn("manage my gas tank", note.content)
        finally:
            db.close()

        duplicate_response = self.client.post(
            "/webhooks/whatsapp/meta",
            content=raw_body,
            headers={
                "content-type": "application/json",
                "x-hub-signature-256": f"sha256={signature}",
            },
        )
        self.assertEqual(duplicate_response.status_code, 200)
        self.assertEqual(duplicate_response.json()["duplicates"], 1)

        db = self.SessionTesting()
        try:
            self.assertEqual(db.query(models.InboundMessage).count(), 1)
            self.assertEqual(db.query(models.Note).count(), 1)
        finally:
            db.close()

    def test_meta_whatsapp_webhook_rejects_bad_signature(self):
        os.environ["BJJ_ENABLE_WHATSAPP_CAPTURE"] = "true"
        os.environ["BJJ_META_APP_SECRET"] = "app-secret"

        response = self.client.post(
            "/webhooks/whatsapp/meta",
            json={"entry": []},
            headers={"x-hub-signature-256": "sha256=bad"},
        )

        self.assertEqual(response.status_code, 401)

    def test_meta_whatsapp_webhook_is_disabled_by_default(self):
        os.environ.pop("BJJ_ENABLE_WHATSAPP_CAPTURE", None)

        response = self.client.get(
            "/webhooks/whatsapp/meta",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "verify-me",
                "hub.challenge": "challenge-123",
            },
        )

        self.assertEqual(response.status_code, 404)

    def _session_for_email(self, email):
        token = self._magic_link_for_email(email)
        session_response = self.client.post("/auth/consume-link", json={"token": token})
        return session_response.json()["session_token"]

    def _magic_link_for_email(self, email):
        previous_value = os.environ.get("BJJ_DEV_AUTH_TOKENS")
        os.environ["BJJ_DEV_AUTH_TOKENS"] = "true"
        try:
            link_response = self.client.post("/auth/request-link", json={"email": email})
            self.assertEqual(link_response.status_code, 200)
            return link_response.json()["dev_token"]
        finally:
            if previous_value is None:
                os.environ.pop("BJJ_DEV_AUTH_TOKENS", None)
            else:
                os.environ["BJJ_DEV_AUTH_TOKENS"] = previous_value

    def _bootstrap_workspace(self):
        response = self.client.post(
            "/workspaces/bootstrap",
            json={
                "gym_name": "Traktion Jiujitsu Academy",
                "owner_email": "owner@example.com",
                "owner_name": "Anthony",
            },
        )
        self.assertEqual(response.status_code, 200)
        return response.json()["invite"]["code"]


if __name__ == "__main__":
    unittest.main()
