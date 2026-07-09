"""Shared fixtures for the BJJ Tracker characterization suite.

This suite is the behavioral contract of the application. It was written
against the v1 backend and verified green there BEFORE the v2 rebuild began;
the rebuild is done only when this suite is green again with zero edits.
"""
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

# Keep the module-level engine away from the repo's real data directory.
_SCRATCH_DB = os.path.join(
    os.environ.get("TMPDIR", "/tmp"), "bjj-tracker-test-suite.db"
)
os.environ.setdefault("BJJ_SQLITE_PATH", _SCRATCH_DB)

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import database  # noqa: E402
import main  # noqa: E402
import models  # noqa: E402  (re-exported for tests)

ENV_PREFIXES = ("BJJ_", "OURA_")


@pytest.fixture(autouse=True)
def clean_env():
    """Isolate every test from ambient BJJ_*/OURA_* configuration."""
    saved = {k: v for k, v in os.environ.items() if k.startswith(ENV_PREFIXES)}
    for key in saved:
        if key != "BJJ_SQLITE_PATH":
            os.environ.pop(key, None)
    yield
    for key in [k for k in os.environ if k.startswith(ENV_PREFIXES)]:
        os.environ.pop(key, None)
    os.environ.update(saved)


@pytest.fixture()
def db_session_factory():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    database.Base.metadata.create_all(bind=engine)
    yield factory
    main.app.dependency_overrides.clear()
    database.Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture()
def client(db_session_factory):
    def override_get_db():
        db = db_session_factory()
        try:
            yield db
        finally:
            db.close()

    main.app.dependency_overrides[database.get_db] = override_get_db
    return TestClient(main.app)


@pytest.fixture()
def db(db_session_factory):
    """Direct handle on the same database the client uses."""
    session = db_session_factory()
    yield session
    session.close()


@pytest.fixture()
def magic_link_for(client):
    def _request(email):
        previous = os.environ.get("BJJ_DEV_AUTH_TOKENS")
        os.environ["BJJ_DEV_AUTH_TOKENS"] = "true"
        try:
            response = client.post("/auth/request-link", json={"email": email})
            assert response.status_code == 200, response.text
            return response.json()["dev_token"]
        finally:
            if previous is None:
                os.environ.pop("BJJ_DEV_AUTH_TOKENS", None)
            else:
                os.environ["BJJ_DEV_AUTH_TOKENS"] = previous

    return _request


@pytest.fixture()
def session_for(client, magic_link_for):
    """Full sign-in flow; returns the session token for an email."""

    def _login(email):
        token = magic_link_for(email)
        response = client.post("/auth/consume-link", json={"token": token})
        assert response.status_code == 200, response.text
        return response.json()["session_token"]

    return _login


@pytest.fixture()
def auth_headers(session_for):
    def _headers(email="athlete@example.com"):
        return {"x-session-token": session_for(email)}

    return _headers


@pytest.fixture()
def bootstrap_workspace(client):
    def _bootstrap(gym_name="Traktion Jiujitsu Academy",
                   owner_email="owner@example.com", owner_name="Anthony"):
        response = client.post(
            "/workspaces/bootstrap",
            json={
                "gym_name": gym_name,
                "owner_email": owner_email,
                "owner_name": owner_name,
            },
        )
        assert response.status_code == 200, response.text
        return response.json()

    return _bootstrap
