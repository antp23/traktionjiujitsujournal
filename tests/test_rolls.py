"""Characterization: /rolls CRUD (session-gated) and roll stats math."""
from datetime import date


def _session(client, headers):
    response = client.post(
        "/sessions", headers=headers,
        json={"date": str(date.today()), "session_type": "gi", "duration_minutes": 60},
    )
    assert response.status_code == 201
    return response.json()["session_id"]


def _roll(client, headers, session_id, partner="Alex", outcome="draw", **overrides):
    payload = {
        "session_id": session_id,
        "partner": partner,
        "gi_nogi": "gi",
        "outcome": outcome,
    }
    payload.update(overrides)
    response = client.post("/rolls", headers=headers, json=payload)
    assert response.status_code == 201, response.text
    return response.json()


class TestCrud:
    def test_requires_auth(self, client):
        assert client.get("/rolls").status_code == 401

    def test_create_requires_owned_session(self, client, auth_headers):
        headers_a = auth_headers("a@example.com")
        headers_b = auth_headers("b@example.com")
        session_b = _session(client, headers_b)

        response = client.post(
            "/rolls", headers=headers_a,
            json={"session_id": session_b, "partner": "X", "gi_nogi": "gi", "outcome": "draw"},
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Session not found"

    def test_create_defaults_and_shape(self, client, auth_headers):
        headers = auth_headers()
        sid = _session(client, headers)
        roll = _roll(client, headers, sid, outcome="submission_win",
                     submission_scored="armbar")
        assert roll["roll_id"]
        assert roll["dominant_positions_held"] == []
        assert roll["dominant_positions_given"] == []
        assert roll["duration_minutes"] is None

    def test_legacy_outcomes_accepted(self, client, auth_headers):
        headers = auth_headers()
        sid = _session(client, headers)
        for outcome in ("win", "loss", "competitive"):
            assert _roll(client, headers, sid, outcome=outcome)["outcome"] == outcome

    def test_validation(self, client, auth_headers):
        headers = auth_headers()
        sid = _session(client, headers)
        base = {"session_id": sid, "partner": "Alex", "gi_nogi": "gi", "outcome": "draw"}
        for bad in (
            {**base, "outcome": "vibes_win"},
            {**base, "gi_nogi": "both"},
            {**base, "duration_minutes": 0},
            {**base, "duration_minutes": 121},
        ):
            assert client.post("/rolls", headers=headers, json=bad).status_code == 422

    def test_get_update_delete_and_isolation(self, client, auth_headers):
        headers_a = auth_headers("a@example.com")
        headers_b = auth_headers("b@example.com")
        sid = _session(client, headers_a)
        roll = _roll(client, headers_a, sid)
        rid = roll["roll_id"]

        assert client.get(f"/rolls/{rid}", headers=headers_a).status_code == 200
        assert client.get(f"/rolls/{rid}", headers=headers_b).status_code == 404

        updated = client.put(f"/rolls/{rid}", headers=headers_a,
                             json={"outcome": "submission_win"})
        assert updated.status_code == 200
        assert updated.json()["outcome"] == "submission_win"
        assert updated.json()["partner"] == "Alex"

        assert client.put(f"/rolls/{rid}", headers=headers_b, json={}).status_code == 404
        assert client.delete(f"/rolls/{rid}", headers=headers_b).status_code == 404
        assert client.delete(f"/rolls/{rid}", headers=headers_a).status_code == 204
        assert client.get(f"/rolls/{rid}", headers=headers_a).status_code == 404

    def test_list_filters(self, client, auth_headers):
        headers = auth_headers()
        sid_1 = _session(client, headers)
        sid_2 = _session(client, headers)
        _roll(client, headers, sid_1, partner="Alexandra")
        _roll(client, headers, sid_2, partner="Blake")

        by_session = client.get("/rolls", headers=headers, params={"session_id": sid_1}).json()
        assert [r["partner"] for r in by_session] == ["Alexandra"]

        by_partner = client.get("/rolls", headers=headers, params={"partner": "alex"}).json()
        assert [r["partner"] for r in by_partner] == ["Alexandra"]


class TestStats:
    def test_empty_stats_shape(self, client, auth_headers):
        stats = client.get("/rolls/stats/summary", headers=auth_headers()).json()
        assert stats == {"total_rolls": 0}

    def test_stats_math(self, client, auth_headers):
        headers = auth_headers()
        sid = _session(client, headers)
        _roll(client, headers, sid, partner="Alex", outcome="submission_win",
              submission_scored="armbar", dominant_positions_held=["mount"])
        _roll(client, headers, sid, partner="Alex", outcome="submission_win",
              submission_scored="armbar")
        _roll(client, headers, sid, partner="Alex", outcome="points_loss",
              submission_received="triangle", dominant_positions_given=["back"])
        _roll(client, headers, sid, partner="Blake", outcome="draw")
        # Legacy outcome: excluded from top-level W/L/draw buckets, but counted
        # as a draw in the per-partner breakdown.
        _roll(client, headers, sid, partner="Blake", outcome="competitive")

        stats = client.get("/rolls/stats/summary", headers=headers).json()
        assert stats["total_rolls"] == 5
        assert stats["wins"] == 2
        assert stats["losses"] == 1
        assert stats["draws"] == 1
        assert stats["win_rate"] == 40.0
        assert stats["top_submissions_scored"] == [["armbar", 2]]
        assert stats["top_submissions_received"] == [["triangle", 1]]
        assert stats["top_positions_held"] == [["mount", 1]]
        assert stats["top_positions_given"] == [["back", 1]]
        assert stats["partner_breakdown"] == {
            "Alex": {"wins": 2, "losses": 1, "draws": 0, "total": 3},
            "Blake": {"wins": 0, "losses": 0, "draws": 2, "total": 2},
        }

    def test_stats_are_user_scoped(self, client, auth_headers):
        headers_a = auth_headers("a@example.com")
        headers_b = auth_headers("b@example.com")
        sid = _session(client, headers_b)
        _roll(client, headers_b, sid)
        assert client.get("/rolls/stats/summary", headers=headers_a).json() == {"total_rolls": 0}
