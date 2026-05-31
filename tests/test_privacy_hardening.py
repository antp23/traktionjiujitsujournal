import pathlib
import sys
import unittest
import os
from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

import database  # noqa: E402
import main  # noqa: E402
import models  # noqa: E402


class PrivacyHardeningTests(unittest.TestCase):
    def setUp(self):
        os.environ["BJJ_DEV_AUTH_TOKENS"] = "true"
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
        self.athlete_a = self._session_for_email("athlete-a@example.com")
        self.athlete_b = self._session_for_email("athlete-b@example.com")

    def tearDown(self):
        main.app.dependency_overrides.clear()
        database.Base.metadata.drop_all(bind=self.engine)

    def test_notes_are_private_to_current_user(self):
        note_a = self.client.post(
            "/notes",
            headers=self._auth(self.athlete_a),
            json={"title": "A note", "content": "A private note"},
        )
        self.assertEqual(note_a.status_code, 201)
        note_id = note_a.json()["note_id"]

        note_b = self.client.post(
            "/notes",
            headers=self._auth(self.athlete_b),
            json={"title": "B note", "content": "B private note"},
        )
        self.assertEqual(note_b.status_code, 201)

        list_a = self.client.get("/notes", headers=self._auth(self.athlete_a))
        self.assertEqual([note["note_id"] for note in list_a.json()], [note_id])

        cross_get = self.client.get(f"/notes/{note_b.json()['note_id']}", headers=self._auth(self.athlete_a))
        self.assertEqual(cross_get.status_code, 404)

        cross_update = self.client.put(
            f"/notes/{note_b.json()['note_id']}",
            headers=self._auth(self.athlete_a),
            json={"content": "stolen"},
        )
        self.assertEqual(cross_update.status_code, 404)

    def test_sessions_are_private_to_current_user(self):
        session_a = self._create_session(self.athlete_a, "A training")
        session_b = self._create_session(self.athlete_b, "B training")

        list_a = self.client.get("/sessions", headers=self._auth(self.athlete_a))
        self.assertEqual([session["session_id"] for session in list_a.json()], [session_a["session_id"]])

        cross_get = self.client.get(f"/sessions/{session_b['session_id']}", headers=self._auth(self.athlete_a))
        self.assertEqual(cross_get.status_code, 404)

        cross_delete = self.client.delete(f"/sessions/{session_b['session_id']}", headers=self._auth(self.athlete_a))
        self.assertEqual(cross_delete.status_code, 404)

    def test_techniques_are_private_to_current_user(self):
        technique_a = self.client.post(
            "/techniques",
            headers=self._auth(self.athlete_a),
            json={"name": "Knee cut", "category": "passing"},
        )
        self.assertEqual(technique_a.status_code, 201)
        technique_b = self.client.post(
            "/techniques",
            headers=self._auth(self.athlete_b),
            json={"name": "Armbar", "category": "submission"},
        )
        self.assertEqual(technique_b.status_code, 201)

        list_a = self.client.get("/techniques", headers=self._auth(self.athlete_a))
        self.assertEqual([technique["technique_id"] for technique in list_a.json()], [technique_a.json()["technique_id"]])

        cross_get = self.client.get(
            f"/techniques/{technique_b.json()['technique_id']}",
            headers=self._auth(self.athlete_a),
        )
        self.assertEqual(cross_get.status_code, 404)

        spotlight = self.client.get("/techniques/spotlight", headers=self._auth(self.athlete_a))
        self.assertEqual(spotlight.status_code, 200)
        self.assertEqual(spotlight.json()["technique_id"], technique_a.json()["technique_id"])

    def test_rolls_and_rank_are_private_to_current_user(self):
        session_a = self._create_session(self.athlete_a, "A training")
        session_b = self._create_session(self.athlete_b, "B training")

        roll_a = self.client.post(
            "/rolls",
            headers=self._auth(self.athlete_a),
            json={
                "session_id": session_a["session_id"],
                "partner": "Alex",
                "gi_nogi": "gi",
                "outcome": "draw",
            },
        )
        self.assertEqual(roll_a.status_code, 201)
        roll_b = self.client.post(
            "/rolls",
            headers=self._auth(self.athlete_b),
            json={
                "session_id": session_b["session_id"],
                "partner": "Blake",
                "gi_nogi": "gi",
                "outcome": "submission_win",
            },
        )
        self.assertEqual(roll_b.status_code, 201)

        cross_session_roll = self.client.post(
            "/rolls",
            headers=self._auth(self.athlete_a),
            json={
                "session_id": session_b["session_id"],
                "partner": "Blake",
                "gi_nogi": "gi",
                "outcome": "draw",
            },
        )
        self.assertEqual(cross_session_roll.status_code, 404)

        list_a = self.client.get("/rolls", headers=self._auth(self.athlete_a))
        self.assertEqual([roll["roll_id"] for roll in list_a.json()], [roll_a.json()["roll_id"]])

        cross_get = self.client.get(f"/rolls/{roll_b.json()['roll_id']}", headers=self._auth(self.athlete_a))
        self.assertEqual(cross_get.status_code, 404)

        rank_a = self.client.post(
            "/rank",
            headers=self._auth(self.athlete_a),
            json={"belt": "blue", "stripes": 1, "date_awarded": str(date.today())},
        )
        self.assertEqual(rank_a.status_code, 201)
        rank_b = self.client.post(
            "/rank",
            headers=self._auth(self.athlete_b),
            json={"belt": "purple", "stripes": 2, "date_awarded": str(date.today())},
        )
        self.assertEqual(rank_b.status_code, 201)

        current_rank_a = self.client.get("/rank/current", headers=self._auth(self.athlete_a))
        self.assertEqual(current_rank_a.status_code, 200)
        self.assertEqual(current_rank_a.json()["rank_id"], rank_a.json()["rank_id"])

        cross_rank_update = self.client.put(
            f"/rank/{rank_b.json()['rank_id']}",
            headers=self._auth(self.athlete_a),
            json={"stripes": 3},
        )
        self.assertEqual(cross_rank_update.status_code, 404)

    def test_parse_and_dashboard_are_authenticated_and_user_scoped(self):
        unauth_parse = self.client.post("/parse", json={"text": "note: no token"})
        self.assertEqual(unauth_parse.status_code, 401)
        unauth_dashboard = self.client.get("/dashboard")
        self.assertEqual(unauth_dashboard.status_code, 401)

        session_a = self._create_session(self.athlete_a, "A training")
        self.client.post(
            "/techniques",
            headers=self._auth(self.athlete_a),
            json={"name": "Tripod sweep", "category": "sweep"},
        )
        self._create_session(self.athlete_b, "B training")
        self.client.post(
            "/techniques",
            headers=self._auth(self.athlete_b),
            json={"name": "Kimura", "category": "submission"},
        )

        parsed = self.client.post(
            "/parse",
            headers=self._auth(self.athlete_a),
            json={"text": "note: keep elbow knee connection"},
        )
        self.assertEqual(parsed.status_code, 200)
        self.assertEqual(parsed.json()["action"], "note_logged")

        notes_b = self.client.get("/notes", headers=self._auth(self.athlete_b))
        self.assertEqual(notes_b.json(), [])

        dashboard_a = self.client.get("/dashboard", headers=self._auth(self.athlete_a))
        self.assertEqual(dashboard_a.status_code, 200)
        payload = dashboard_a.json()
        self.assertEqual(payload["session_stats"]["total_sessions"], 1)
        self.assertEqual(payload["total_techniques"], 1)
        self.assertEqual(payload["recent_sessions"][0]["session_id"], session_a["session_id"])
        self.assertEqual(payload["spotlight"]["name"], "Tripod sweep")

    def _create_session(self, session_token, focus_area):
        response = self.client.post(
            "/sessions",
            headers=self._auth(session_token),
            json={
                "date": str(date.today()),
                "session_type": "gi",
                "duration_minutes": 60,
                "focus_area": focus_area,
            },
        )
        self.assertEqual(response.status_code, 201)
        return response.json()

    def _session_for_email(self, email):
        link_response = self.client.post("/auth/request-link", json={"email": email})
        token = link_response.json()["dev_token"]
        session_response = self.client.post("/auth/consume-link", json={"token": token})
        return session_response.json()["session_token"]

    def _auth(self, session_token):
        return {"x-session-token": session_token}


if __name__ == "__main__":
    unittest.main()
