"""Characterization: magic-link auth, sessions, throttling, email delivery."""
import os
from datetime import datetime, timedelta
from unittest.mock import patch

import models

SAFE_MESSAGE = "If the email is allowed, a sign-in link will be sent."


def _smtp_env():
    os.environ.update({
        "BJJ_FRONTEND_URL": "https://bjj.example.com",
        "BJJ_EMAIL_FROM": "BJJ Tracker <no-reply@bjj.example.com>",
        "BJJ_SMTP_HOST": "smtp.example.com",
        "BJJ_SMTP_PORT": "465",
        "BJJ_SMTP_USERNAME": "smtp-user",
        "BJJ_SMTP_PASSWORD": "smtp-pass",
        "BJJ_SMTP_USE_SSL": "true",
    })


class TestRequestLink:
    def test_unconfigured_login_returns_503(self, client):
        response = client.post("/auth/request-link", json={"email": "a@example.com"})
        assert response.status_code == 503
        assert response.json()["detail"] == "Email login is not configured"

    def test_dev_token_mode(self, client):
        os.environ["BJJ_DEV_AUTH_TOKENS"] = "true"
        response = client.post("/auth/request-link", json={"email": "a@example.com"})
        assert response.status_code == 200
        body = response.json()
        assert body["message"] == SAFE_MESSAGE
        assert isinstance(body["dev_token"], str) and body["dev_token"]

    def test_smtp_send_includes_login_link(self, client):
        _smtp_env()
        with patch("smtplib.SMTP_SSL") as smtp_ssl:
            response = client.post(
                "/auth/request-link", json={"email": "Athlete@Example.com "}
            )
        assert response.status_code == 200
        assert response.json()["dev_token"] is None
        smtp_ssl.assert_called_once_with("smtp.example.com", 465, timeout=10)
        smtp = smtp_ssl.return_value.__enter__.return_value
        smtp.login.assert_called_once_with("smtp-user", "smtp-pass")
        message = smtp.send_message.call_args.args[0]
        # Email is normalized (trimmed + lowercased) before use.
        assert message["To"] == "athlete@example.com"
        assert "Sign in to BJJ Tracker" in message["Subject"]
        body = message.get_body(preferencelist=("plain",)).get_content()
        assert "https://bjj.example.com/login?token=" in body
        assert "None" not in body

    def test_smtp_failure_returns_502(self, client):
        _smtp_env()
        with patch("smtplib.SMTP_SSL", side_effect=OSError("boom")):
            response = client.post(
                "/auth/request-link", json={"email": "a@example.com"}
            )
        assert response.status_code == 502
        assert response.json()["detail"] == "Could not send sign-in email"

    def test_throttled_per_email_case_insensitive(self, client):
        os.environ["BJJ_DEV_AUTH_TOKENS"] = "true"
        os.environ["BJJ_AUTH_REQUEST_LIMIT"] = "2"
        assert client.post("/auth/request-link", json={"email": "a@example.com"}).status_code == 200
        assert client.post("/auth/request-link", json={"email": "A@EXAMPLE.com"}).status_code == 200
        throttled = client.post("/auth/request-link", json={"email": "a@example.com"})
        assert throttled.status_code == 429
        assert "Too many sign-in link requests" in throttled.json()["detail"]
        # A different email is unaffected.
        assert client.post("/auth/request-link", json={"email": "b@example.com"}).status_code == 200

    def test_throttle_window_expires(self, client, db):
        os.environ["BJJ_DEV_AUTH_TOKENS"] = "true"
        os.environ["BJJ_AUTH_REQUEST_LIMIT"] = "1"
        os.environ["BJJ_AUTH_REQUEST_WINDOW_MINUTES"] = "15"
        assert client.post("/auth/request-link", json={"email": "a@example.com"}).status_code == 200
        assert client.post("/auth/request-link", json={"email": "a@example.com"}).status_code == 429
        token = db.query(models.AuthToken).filter(models.AuthToken.email == "a@example.com").one()
        token.created_at = datetime.utcnow() - timedelta(minutes=16)
        db.commit()
        assert client.post("/auth/request-link", json={"email": "a@example.com"}).status_code == 200


class TestConsumeLink:
    def test_consume_creates_user_and_session(self, client, magic_link_for):
        token = magic_link_for("new-user@example.com")
        response = client.post("/auth/consume-link", json={"token": token})
        assert response.status_code == 200
        body = response.json()
        assert body["session_token"]
        assert body["user"]["email"] == "new-user@example.com"
        assert set(body["user"]) == {"user_id", "email", "name", "preferred_name"}

    def test_consume_is_single_use(self, client, magic_link_for):
        token = magic_link_for("a@example.com")
        assert client.post("/auth/consume-link", json={"token": token}).status_code == 200
        second = client.post("/auth/consume-link", json={"token": token})
        assert second.status_code == 400
        assert second.json()["detail"] == "Invalid or consumed token"

    def test_unknown_token_rejected(self, client):
        response = client.post("/auth/consume-link", json={"token": "nope"})
        assert response.status_code == 400

    def test_session_token_cannot_be_consumed_as_magic_link(self, client, session_for):
        session_token = session_for("a@example.com")
        response = client.post("/auth/consume-link", json={"token": session_token})
        assert response.status_code == 400

    def test_expired_magic_link_rejected(self, client, magic_link_for, db):
        token = magic_link_for("a@example.com")
        row = db.query(models.AuthToken).filter(models.AuthToken.token == token).one()
        row.expires_at = datetime.utcnow() - timedelta(minutes=1)
        db.commit()
        response = client.post("/auth/consume-link", json={"token": token})
        assert response.status_code == 400
        assert "expired" in response.json()["detail"].lower()

    def test_returning_user_is_reused(self, client, session_for, db):
        session_for("a@example.com")
        session_for("a@example.com")
        assert db.query(models.User).filter(models.User.email == "a@example.com").count() == 1


class TestSessions:
    def test_me_requires_token(self, client):
        response = client.get("/auth/me")
        assert response.status_code == 401
        assert response.json()["detail"] == "Missing session token"

    def test_me_rejects_unknown_token(self, client):
        response = client.get("/auth/me", headers={"x-session-token": "junk"})
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid session token"

    def test_me_shape_for_fresh_user(self, client, auth_headers):
        response = client.get("/auth/me", headers=auth_headers("a@example.com"))
        assert response.status_code == 200
        body = response.json()
        assert body["user"]["email"] == "a@example.com"
        assert body["memberships"] == []
        assert body["profile"] is None

    def test_expired_session_rejected(self, client, session_for, db):
        token = session_for("a@example.com")
        row = db.query(models.AuthToken).filter(models.AuthToken.token == token).one()
        row.expires_at = datetime.utcnow() - timedelta(minutes=1)
        db.commit()
        response = client.get("/auth/me", headers={"x-session-token": token})
        assert response.status_code == 401
        assert "expired" in response.json()["detail"].lower()

    def test_logout_revokes_session(self, client, session_for):
        token = session_for("a@example.com")
        headers = {"x-session-token": token}
        response = client.post("/auth/logout", headers=headers)
        assert response.status_code == 200
        assert response.json() == {"message": "Logged out."}
        followup = client.get("/auth/me", headers=headers)
        assert followup.status_code == 401
        assert followup.json()["detail"] == "Revoked session token"

    def test_logout_requires_session(self, client):
        assert client.post("/auth/logout").status_code == 401
