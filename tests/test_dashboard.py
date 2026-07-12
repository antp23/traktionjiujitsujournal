"""Characterization: the /dashboard aggregate payload."""
from datetime import date


class TestDashboard:
    def test_requires_auth(self, client):
        assert client.get("/dashboard").status_code == 401

    def test_empty_state_shape(self, client, auth_headers):
        payload = client.get("/dashboard", headers=auth_headers()).json()
        assert set(payload) == {
            "session_stats", "current_rank", "technique_counts",
            "total_techniques", "recent_sessions", "roll_stats", "spotlight",
        }
        assert payload["current_rank"] == {"belt": None, "stripes": 0, "date_awarded": None}
        assert payload["technique_counts"] == {}
        assert payload["total_techniques"] == 0
        assert payload["recent_sessions"] == []
        assert payload["roll_stats"] == {"total_rolls": 0}
        assert payload["spotlight"] is None
        assert payload["session_stats"]["total_sessions"] == 0

    def test_populated_dashboard_is_user_scoped(self, client, auth_headers):
        headers = auth_headers("a@example.com")
        other = auth_headers("b@example.com")

        # Six sessions: recent list caps at five, newest first.
        for day in range(1, 7):
            response = client.post("/sessions", headers=headers, json={
                "date": f"2026-07-0{day}", "session_type": "gi",
                "duration_minutes": 60, "focus_area": f"day {day}",
            })
            assert response.status_code == 201

        client.post("/rank", headers=headers,
                    json={"belt": "purple", "stripes": 2, "date_awarded": "2025-06-01"})
        client.post("/rank", headers=headers,
                    json={"belt": "blue", "stripes": 4, "date_awarded": "2023-01-01"})
        client.post("/techniques", headers=headers,
                    json={"name": "Tripod sweep", "category": "sweep"})
        client.post("/techniques", headers=headers,
                    json={"name": "Kimura", "category": "submission",
                          "proficiency": "sharp"})

        # Noise from another user must not leak in.
        client.post("/sessions", headers=other, json={
            "date": str(date.today()), "session_type": "no-gi", "duration_minutes": 60,
        })
        client.post("/techniques", headers=other,
                    json={"name": "Heel hook", "category": "leglock"})

        payload = client.get("/dashboard", headers=headers).json()

        assert payload["current_rank"] == {
            "belt": "purple", "stripes": 2, "date_awarded": "2025-06-01",
        }
        assert payload["total_techniques"] == 2
        assert payload["technique_counts"] == {"learning": 1, "sharp": 1}

        recents = payload["recent_sessions"]
        assert len(recents) == 5
        assert [s["date"] for s in recents] == [
            "2026-07-06", "2026-07-05", "2026-07-04", "2026-07-03", "2026-07-02",
        ]
        assert set(recents[0]) == {
            "session_id", "date", "session_type", "duration_minutes",
            "focus_area", "attended",
        }

        # Spotlight prefers learning/drilling techniques.
        assert payload["spotlight"]["name"] == "Tripod sweep"
        assert set(payload["spotlight"]) == {
            "technique_id", "name", "category", "proficiency", "position",
        }

        assert payload["session_stats"]["total_sessions"] == 6
