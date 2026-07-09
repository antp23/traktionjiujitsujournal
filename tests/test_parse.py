"""Characterization: the /parse quick-log natural language heuristics."""
from datetime import date, timedelta


def _parse(client, headers, text):
    response = client.post("/parse", headers=headers, json={"text": text})
    assert response.status_code == 200, response.text
    return response.json()


class TestGuards:
    def test_requires_auth(self, client):
        assert client.post("/parse", json={"text": "note: hi"}).status_code == 401

    def test_empty_input(self, client, auth_headers):
        result = _parse(client, auth_headers(), "   ")
        assert result == {"success": False, "action": None,
                          "message": "Empty input.", "data": None}


class TestSessionIntent:
    def test_no_gi_session_with_focus_and_duration(self, client, auth_headers):
        headers = auth_headers()
        result = _parse(client, headers, "trained 1hr no gi, worked on guard passing")
        assert result["success"] is True
        assert result["action"] == "session_logged"
        assert result["message"].startswith("Session logged: No Gi, 60min")
        assert "guard passing" in result["message"]

        session = client.get(f"/sessions/{result['data']['session_id']}", headers=headers).json()
        assert session["session_type"] == "no-gi"
        assert session["duration_minutes"] == 60
        assert session["focus_area"] == "guard passing"
        assert session["date"] == str(date.today())
        assert session["gym_location"] == "Traktion Jiu Jitsu Academy"
        assert session["attended"] is True

    def test_yesterday_and_fractional_hours(self, client, auth_headers):
        headers = auth_headers()
        result = _parse(client, headers, "trained 1.5 hours gi yesterday")
        session = client.get(f"/sessions/{result['data']['session_id']}", headers=headers).json()
        assert session["date"] == str(date.today() - timedelta(days=1))
        assert session["duration_minutes"] == 90
        assert session["session_type"] == "gi"

    def test_last_weekday(self, client, auth_headers):
        headers = auth_headers()
        result = _parse(client, headers, "trained gi last monday")
        session = client.get(f"/sessions/{result['data']['session_id']}", headers=headers).json()
        logged = date.fromisoformat(session["date"])
        assert logged.weekday() == 0
        assert 1 <= (date.today() - logged).days <= 7

    def test_minutes_and_energy_words(self, client, auth_headers):
        headers = auth_headers()
        result = _parse(client, headers, "45 min drilling session, felt gassed")
        session = client.get(f"/sessions/{result['data']['session_id']}", headers=headers).json()
        assert session["duration_minutes"] == 45
        assert session["session_type"] == "drilling"
        assert session["energy_level"] == 3

    def test_great_energy_and_default_duration(self, client, auth_headers):
        headers = auth_headers()
        result = _parse(client, headers, "just got back from class, felt great")
        session = client.get(f"/sessions/{result['data']['session_id']}", headers=headers).json()
        assert session["duration_minutes"] == 60
        assert session["energy_level"] == 9

    def test_explicit_notes_suffix(self, client, auth_headers):
        headers = auth_headers()
        result = _parse(client, headers, "trained gi. notes: guard felt sticky today")
        session = client.get(f"/sessions/{result['data']['session_id']}", headers=headers).json()
        assert session["notes"] == "guard felt sticky today"

    def test_raw_text_becomes_notes_when_no_notes_marker(self, client, auth_headers):
        headers = auth_headers()
        text = "trained 30 min gi"
        result = _parse(client, headers, text)
        session = client.get(f"/sessions/{result['data']['session_id']}", headers=headers).json()
        assert session["notes"] == text


class TestNoteIntent:
    def test_note_prefix_is_stripped(self, client, auth_headers):
        headers = auth_headers()
        result = _parse(client, headers, "note: keep elbow knee connection")
        assert result["action"] == "note_logged"
        assert "keep elbow knee connection" in result["message"]

        notes = client.get("/notes", headers=headers).json()
        assert len(notes) == 1
        assert notes[0]["content"] == "keep elbow knee connection"
        assert notes[0]["tags"] == ["quick-log"]

    def test_remember_trigger(self, client, auth_headers):
        headers = auth_headers()
        result = _parse(client, headers, "remember to stretch hips daily")
        assert result["action"] == "note_logged"


class TestTechniqueIntent:
    def test_learned_creates_technique(self, client, auth_headers):
        headers = auth_headers()
        result = _parse(client, headers, "learned a berimbolo")
        assert result["action"] == "technique_logged"
        technique = client.get(
            f"/techniques/{result['data']['technique_id']}", headers=headers
        ).json()
        assert technique["name"] == "Berimbolo"
        assert technique["category"] == "General"
        assert technique["proficiency"] == "learning"

    def test_existing_technique_is_detected(self, client, auth_headers):
        headers = auth_headers()
        client.post("/techniques", headers=headers,
                    json={"name": "Berimbolo", "category": "guard",
                          "proficiency": "drilling"})
        result = _parse(client, headers, "learned a berimbolo")
        assert result["action"] == "technique_exists"
        assert "drilling" in result["message"]


class TestFallback:
    def test_unknown_text_becomes_raw_capture(self, client, auth_headers):
        headers = auth_headers()
        result = _parse(client, headers, "random thoughts about lunch")
        assert result["action"] == "raw_capture_logged"
        notes = client.get("/notes", headers=headers).json()
        assert notes[0]["title"] == "Quick Log capture"
        assert notes[0]["content"] == "random thoughts about lunch"
        assert notes[0]["tags"] == ["quick-log", "unparsed"]

    def test_parse_writes_are_user_scoped(self, client, auth_headers):
        headers_a = auth_headers("a@example.com")
        headers_b = auth_headers("b@example.com")
        _parse(client, headers_a, "note: private thought")
        assert client.get("/notes", headers=headers_b).json() == []
