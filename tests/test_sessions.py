"""Characterization: /sessions CRUD, filtering, validation, and stats math."""
from datetime import date, timedelta


def _make(client, headers, **overrides):
    payload = {"date": str(date.today()), "session_type": "gi", "duration_minutes": 60}
    payload.update(overrides)
    response = client.post("/sessions", headers=headers, json=payload)
    assert response.status_code == 201, response.text
    return response.json()


class TestCrud:
    def test_requires_auth(self, client):
        assert client.get("/sessions").status_code == 401
        assert client.post("/sessions", json={}).status_code == 401

    def test_create_defaults(self, client, auth_headers):
        headers = auth_headers()
        created = _make(client, headers, date="2026-07-01")
        assert created["session_id"]
        assert created["created_at"]
        assert created["duration_minutes"] == 60
        assert created["attended"] is True
        assert created["partners"] == []
        assert created["gym_location"] is None
        assert created["energy_level"] is None
        assert created["rounds_rolled"] is None

    def test_validation_bounds(self, client, auth_headers):
        headers = auth_headers()
        base = {"date": "2026-07-01", "session_type": "gi"}
        for bad in (
            {**base, "duration_minutes": 0},
            {**base, "duration_minutes": 481},
            {**base, "energy_level": 11},
            {**base, "energy_level": 0},
            {**base, "rounds_rolled": -1},
            {**base, "rounds_rolled": 101},
            {**base, "session_type": "wrestling"},
        ):
            assert client.post("/sessions", headers=headers, json=bad).status_code == 422

    def test_get_update_delete(self, client, auth_headers):
        headers = auth_headers()
        created = _make(client, headers, notes="original", focus_area="guard")
        sid = created["session_id"]

        assert client.get(f"/sessions/{sid}", headers=headers).json()["notes"] == "original"

        # Partial update leaves unspecified fields alone (exclude_unset).
        updated = client.put(f"/sessions/{sid}", headers=headers, json={"notes": "changed"})
        assert updated.status_code == 200
        assert updated.json()["notes"] == "changed"
        assert updated.json()["focus_area"] == "guard"

        assert client.delete(f"/sessions/{sid}", headers=headers).status_code == 204
        assert client.get(f"/sessions/{sid}", headers=headers).status_code == 404

    def test_missing_id_is_404(self, client, auth_headers):
        headers = auth_headers()
        assert client.get("/sessions/nope", headers=headers).status_code == 404
        assert client.put("/sessions/nope", headers=headers, json={}).status_code == 404
        assert client.delete("/sessions/nope", headers=headers).status_code == 404

    def test_cross_user_isolation(self, client, auth_headers):
        headers_a = auth_headers("a@example.com")
        headers_b = auth_headers("b@example.com")
        session_b = _make(client, headers_b)

        assert client.get("/sessions", headers=headers_a).json() == []
        sid = session_b["session_id"]
        assert client.get(f"/sessions/{sid}", headers=headers_a).status_code == 404
        assert client.put(f"/sessions/{sid}", headers=headers_a, json={}).status_code == 404
        assert client.delete(f"/sessions/{sid}", headers=headers_a).status_code == 404


class TestListFilters:
    def test_filters_and_ordering(self, client, auth_headers):
        headers = auth_headers()
        _make(client, headers, date="2026-07-01", session_type="gi", gym_location="HQ")
        _make(client, headers, date="2026-07-03", session_type="no-gi", gym_location="HQ")
        _make(client, headers, date="2026-07-02", session_type="gi", gym_location="Annex")

        listed = client.get("/sessions", headers=headers).json()
        assert [s["date"] for s in listed] == ["2026-07-03", "2026-07-02", "2026-07-01"]

        gi_only = client.get("/sessions", headers=headers, params={"session_type": "gi"}).json()
        assert {s["date"] for s in gi_only} == {"2026-07-01", "2026-07-02"}

        hq = client.get("/sessions", headers=headers, params={"gym_location": "HQ"}).json()
        assert len(hq) == 2

        ranged = client.get(
            "/sessions", headers=headers,
            params={"date_from": "2026-07-02", "date_to": "2026-07-02"},
        ).json()
        assert [s["date"] for s in ranged] == ["2026-07-02"]

        limited = client.get("/sessions", headers=headers, params={"limit": 1}).json()
        assert len(limited) == 1

    def test_limit_bounds(self, client, auth_headers):
        headers = auth_headers()
        assert client.get("/sessions", headers=headers, params={"limit": 0}).status_code == 422
        assert client.get("/sessions", headers=headers, params={"limit": 501}).status_code == 422


class TestStats:
    def test_empty_stats(self, client, auth_headers):
        stats = client.get("/sessions/stats/summary", headers=auth_headers()).json()
        assert stats == {
            "total_sessions": 0,
            "total_minutes": 0,
            "sessions_this_week": 0,
            "sessions_this_month": 0,
            "current_streak": 0,
            "last_30_day_count": 0,
            "last_90_day_count": 0,
            "last_30_day_rate": 0.0,
            "last_90_day_rate": 0.0,
        }

    def test_attendance_and_streak_math(self, client, auth_headers):
        headers = auth_headers()
        today = date.today()
        week_start = today - timedelta(days=today.weekday())

        # Three consecutive training weeks, then a gap week, then an older week.
        _make(client, headers, date=str(today), duration_minutes=90)
        _make(client, headers, date=str(week_start - timedelta(days=3)), duration_minutes=60)
        _make(client, headers, date=str(week_start - timedelta(days=10)), duration_minutes=30)
        _make(client, headers, date=str(week_start - timedelta(days=22)), duration_minutes=45)
        # Missed classes never count.
        _make(client, headers, date=str(today), duration_minutes=60, attended=False)

        stats = client.get("/sessions/stats/summary", headers=headers).json()
        assert stats["total_sessions"] == 4
        assert stats["total_minutes"] == 90 + 60 + 30 + 45
        assert stats["sessions_this_week"] == 1
        assert stats["current_streak"] == 3
        assert stats["last_30_day_count"] == 4
        assert stats["last_90_day_count"] == 4
        assert stats["last_30_day_rate"] == round(4 / 30 * 7, 1)
        assert stats["last_90_day_rate"] == round(4 / 90 * 7, 1)

    def test_streak_is_zero_without_a_session_this_week(self, client, auth_headers):
        headers = auth_headers()
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        _make(client, headers, date=str(week_start - timedelta(days=2)))
        stats = client.get("/sessions/stats/summary", headers=headers).json()
        assert stats["current_streak"] == 0
        assert stats["sessions_this_week"] == 0
