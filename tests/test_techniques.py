"""Characterization: /techniques CRUD, filters, spotlight, and links."""
from datetime import date


def _make(client, headers, name="Armbar", category="submission", **overrides):
    payload = {"name": name, "category": category}
    payload.update(overrides)
    response = client.post("/techniques", headers=headers, json=payload)
    assert response.status_code == 201, response.text
    return response.json()


class TestCrud:
    def test_requires_auth(self, client):
        assert client.get("/techniques").status_code == 401

    def test_create_defaults(self, client, auth_headers):
        created = _make(client, auth_headers())
        assert created["technique_id"]
        assert created["gi_nogi"] == "both"
        assert created["proficiency"] == "learning"
        assert created["date_added"] == str(date.today())
        for field in ("key_details", "common_mistakes", "counters",
                      "counters_to_counters", "video_urls", "tags"):
            assert created[field] == []

    def test_legacy_no_gi_spelling_accepted(self, client, auth_headers):
        created = _make(client, auth_headers(), gi_nogi="no_gi")
        assert created["gi_nogi"] == "no_gi"

    def test_invalid_proficiency_rejected(self, client, auth_headers):
        response = client.post(
            "/techniques", headers=auth_headers(),
            json={"name": "X", "category": "y", "proficiency": "mastered"},
        )
        assert response.status_code == 422

    def test_update_is_partial(self, client, auth_headers):
        headers = auth_headers()
        created = _make(client, headers, notes="keep", proficiency="drilling")
        tid = created["technique_id"]
        updated = client.put(
            f"/techniques/{tid}", headers=headers, json={"last_drilled": "2026-07-01"}
        )
        assert updated.status_code == 200
        assert updated.json()["last_drilled"] == "2026-07-01"
        assert updated.json()["notes"] == "keep"
        assert updated.json()["proficiency"] == "drilling"

    def test_delete(self, client, auth_headers):
        headers = auth_headers()
        tid = _make(client, headers)["technique_id"]
        assert client.delete(f"/techniques/{tid}", headers=headers).status_code == 204
        assert client.get(f"/techniques/{tid}", headers=headers).status_code == 404

    def test_cross_user_isolation(self, client, auth_headers):
        headers_a = auth_headers("a@example.com")
        headers_b = auth_headers("b@example.com")
        theirs = _make(client, headers_b)
        assert client.get("/techniques", headers=headers_a).json() == []
        assert client.get(f"/techniques/{theirs['technique_id']}", headers=headers_a).status_code == 404


class TestListFilters:
    def test_filters(self, client, auth_headers):
        headers = auth_headers()
        _make(client, headers, name="Knee Cut", category="passing",
              position="Half Guard Top", gi_nogi="both", proficiency="sharp",
              tags=["passing", "pressure"])
        _make(client, headers, name="Berimbolo", category="guard",
              position="De La Riva", gi_nogi="gi", proficiency="learning",
              tags=["inversion"])

        by_category = client.get("/techniques", headers=headers, params={"category": "guard"}).json()
        assert [t["name"] for t in by_category] == ["Berimbolo"]

        by_position = client.get("/techniques", headers=headers, params={"position": "half"}).json()
        assert [t["name"] for t in by_position] == ["Knee Cut"]

        by_format = client.get("/techniques", headers=headers, params={"gi_nogi": "gi"}).json()
        assert [t["name"] for t in by_format] == ["Berimbolo"]

        by_prof = client.get("/techniques", headers=headers, params={"proficiency": "sharp"}).json()
        assert [t["name"] for t in by_prof] == ["Knee Cut"]

        by_tag = client.get("/techniques", headers=headers, params={"tag": "pressure"}).json()
        assert [t["name"] for t in by_tag] == ["Knee Cut"]

        by_search = client.get("/techniques", headers=headers, params={"search": "bolo"}).json()
        assert [t["name"] for t in by_search] == ["Berimbolo"]

    def test_sort_variants(self, client, auth_headers):
        headers = auth_headers()
        _make(client, headers, name="Old Drill", last_drilled="2026-01-01",
              last_hit_in_roll="2026-06-01")
        _make(client, headers, name="Fresh Drill", last_drilled="2026-07-01",
              last_hit_in_roll="2026-02-01")
        _make(client, headers, name="Never Drilled")

        by_drilled = client.get("/techniques", headers=headers, params={"sort": "last_drilled"}).json()
        assert [t["name"] for t in by_drilled] == ["Fresh Drill", "Old Drill", "Never Drilled"]

        by_hit = client.get("/techniques", headers=headers, params={"sort": "last_hit"}).json()
        assert [t["name"] for t in by_hit] == ["Old Drill", "Fresh Drill", "Never Drilled"]


class TestSpotlight:
    def test_prefers_learning_and_drilling(self, client, auth_headers):
        headers = auth_headers()
        _make(client, headers, name="Sharp One", proficiency="sharp")
        _make(client, headers, name="Learner", proficiency="learning")
        spotlight = client.get("/techniques/spotlight", headers=headers)
        assert spotlight.status_code == 200
        assert spotlight.json()["name"] == "Learner"

    def test_falls_back_to_any_technique(self, client, auth_headers):
        headers = auth_headers()
        _make(client, headers, name="Sharp One", proficiency="sharp")
        spotlight = client.get("/techniques/spotlight", headers=headers)
        assert spotlight.json()["name"] == "Sharp One"

    def test_404_when_library_empty(self, client, auth_headers):
        response = client.get("/techniques/spotlight", headers=auth_headers())
        assert response.status_code == 404
        assert response.json()["detail"] == "No techniques found"


class TestLinks:
    def test_link_and_unlink(self, client, auth_headers):
        headers = auth_headers()
        a = _make(client, headers, name="Setup")["technique_id"]
        b = _make(client, headers, name="Finish")["technique_id"]

        linked = client.post(
            f"/techniques/{a}/link", headers=headers,
            json={"to_technique_id": b, "relationship_type": "setup"},
        )
        assert linked.status_code == 201
        assert linked.json() == {"status": "linked"}

        assert client.delete(f"/techniques/{a}/link/{b}", headers=headers).status_code == 204
        # Unlinking again is a no-op, not an error.
        assert client.delete(f"/techniques/{a}/link/{b}", headers=headers).status_code == 204

    def test_link_rejects_unknown_or_foreign_targets(self, client, auth_headers):
        headers_a = auth_headers("a@example.com")
        headers_b = auth_headers("b@example.com")
        mine = _make(client, headers_a)["technique_id"]
        theirs = _make(client, headers_b)["technique_id"]

        for target in ("missing", theirs):
            response = client.post(
                f"/techniques/{mine}/link", headers=headers_a,
                json={"to_technique_id": target},
            )
            assert response.status_code == 404

    def test_link_validates_relationship_type(self, client, auth_headers):
        headers = auth_headers()
        a = _make(client, headers)["technique_id"]
        b = _make(client, headers, name="Other")["technique_id"]
        response = client.post(
            f"/techniques/{a}/link", headers=headers,
            json={"to_technique_id": b, "relationship_type": "sibling"},
        )
        assert response.status_code == 422
