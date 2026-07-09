"""Characterization: coaches (unauthenticated), Oura storage endpoints,
API-key middleware, health, schema quirks, and the SQLite column back-fill."""
import os
from datetime import date, datetime, timedelta

from sqlalchemy import inspect, text

import database
import main
import models
import schemas
from models import OuraDaily, OuraToken


class TestCoaches:
    """v1 quirk (kept deliberately): /coaches has no user auth and no ownership."""

    def test_crud_without_authentication(self, client):
        assert client.get("/coaches").json() == []

        created = client.post("/coaches", json={"name": "Prof. Silva", "belt": "black"})
        assert created.status_code == 201
        coach = created.json()
        assert coach["coach_id"]
        assert coach["date_added"] == str(date.today())
        assert coach["gym"] is None

        cid = coach["coach_id"]
        fetched = client.get(f"/coaches/{cid}")
        assert fetched.status_code == 200
        assert fetched.json()["name"] == "Prof. Silva"

        updated = client.put(f"/coaches/{cid}", json={"gym": "Traktion"})
        assert updated.json()["gym"] == "Traktion"
        assert updated.json()["name"] == "Prof. Silva"

        assert client.delete(f"/coaches/{cid}").status_code == 204
        assert client.get(f"/coaches/{cid}").status_code == 404


class TestHealthAndApiKey:
    def test_health(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_api_key_guards_only_non_session_routes(self, client, auth_headers):
        headers = auth_headers()
        os.environ["BJJ_TRACKER_API_KEY"] = "sekrit"

        # Public paths stay open.
        assert client.get("/health").status_code == 200
        # Session-auth prefixes bypass the API key (session token is the guard).
        assert client.get("/sessions", headers=headers).status_code == 200
        # Everything else (e.g. /coaches, /oura) needs the key.
        denied = client.get("/coaches")
        assert denied.status_code == 401
        assert denied.json() == {"detail": "Invalid or missing API key"}
        assert client.get("/coaches", headers={"x-api-key": "wrong"}).status_code == 401
        assert client.get("/coaches", headers={"x-api-key": "sekrit"}).status_code == 200

    def test_no_api_key_configured_means_open(self, client):
        assert client.get("/coaches").status_code == 200


class TestOuraStorage:
    """Oura endpoints use the process-global engine (v1 quirk, kept)."""

    def setup_method(self):
        database.Base.metadata.create_all(bind=database.engine)
        with database.SessionLocal() as session:
            session.query(OuraDaily).delete()
            session.query(OuraToken).delete()
            session.commit()

    teardown_method = setup_method

    def test_status_reflects_stored_token(self, client):
        assert client.get("/oura/status").json() == {"connected": False}

        with database.SessionLocal() as session:
            session.add(OuraToken(access_token="a", refresh_token="r"))
            session.commit()

        status = client.get("/oura/status").json()
        assert status["connected"] is True
        assert status["updated_at"]

    def test_data_returns_recent_days_newest_first(self, client):
        today = date.today()
        with database.SessionLocal() as session:
            session.add(OuraDaily(date=str(today), readiness_score=82,
                                  sleep_score=75, hrv_avg=64, resting_hr=52,
                                  total_sleep_minutes=431))
            session.add(OuraDaily(date=str(today - timedelta(days=2)),
                                  readiness_score=55))
            session.add(OuraDaily(date=str(today - timedelta(days=90)),
                                  readiness_score=90))
            session.commit()

        rows = client.get("/oura/data", params={"days": 30}).json()
        assert [r["date"] for r in rows] == [str(today), str(today - timedelta(days=2))]
        assert rows[0] == {
            "date": str(today), "readiness_score": 82, "sleep_score": 75,
            "hrv_avg": 64, "resting_hr": 52, "total_sleep_minutes": 431,
            "temperature_deviation": None,
        }


class TestSchemaQuirks:
    def test_legacy_seed_values_still_serialize(self):
        technique = schemas.TechniqueResponse(
            technique_id="tech-1", name="Knee cut", category="passing",
            direction="left", gi_nogi="no_gi", date_added="2026-05-17",
        )
        roll = schemas.RollLogResponse(
            roll_id="roll-1", session_id="session-1", partner="Alex",
            gi_nogi="gi", outcome="competitive",
        )
        assert technique.gi_nogi == "no_gi"
        assert roll.outcome == "competitive"

    def test_mutable_list_defaults_are_isolated(self):
        first = schemas.TechniqueCreate(name="Armbar", category="submission")
        second = schemas.TechniqueCreate(name="Triangle", category="submission")
        first.tags.append("guard")
        assert second.tags == []


class TestSqliteBackfillMigration:
    """The startup migration adds columns that pre-auth databases lack."""

    def _reset_global_db(self):
        database.Base.metadata.drop_all(bind=database.engine)

    def test_owner_and_expiry_columns_are_backfilled(self):
        self._reset_global_db()
        with database.engine.connect() as connection:
            connection.exec_driver_sql(
                "CREATE TABLE notes (note_id VARCHAR PRIMARY KEY, content TEXT)"
            )
            connection.exec_driver_sql(
                "CREATE TABLE auth_tokens ("
                "token VARCHAR PRIMARY KEY, email VARCHAR, user_id VARCHAR, "
                "token_type VARCHAR, consumed_at DATETIME, created_at DATETIME)"
            )
            connection.exec_driver_sql(
                "INSERT INTO auth_tokens (token, email, token_type, created_at) "
                "VALUES ('t-session', 'a@example.com', 'session', '2026-05-01 00:00:00'), "
                "('t-magic', 'a@example.com', 'magic_link', '2026-05-01 00:00:00')"
            )
            connection.commit()

        main._ensure_nullable_columns()

        inspector = inspect(database.engine)
        note_columns = {c["name"] for c in inspector.get_columns("notes")}
        assert "owner_user_id" in note_columns
        token_columns = {c["name"] for c in inspector.get_columns("auth_tokens")}
        assert "expires_at" in token_columns

        with database.engine.connect() as connection:
            rows = dict(connection.execute(
                text("SELECT token, expires_at FROM auth_tokens")
            ).fetchall())
        session_expiry = datetime.fromisoformat(rows["t-session"])
        magic_expiry = datetime.fromisoformat(rows["t-magic"])
        assert session_expiry - magic_expiry == timedelta(days=30) - timedelta(minutes=15)

        # Running it again is a no-op.
        main._ensure_nullable_columns()

        self._reset_global_db()
        database.Base.metadata.create_all(bind=database.engine)
