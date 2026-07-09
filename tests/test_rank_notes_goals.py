"""Characterization: /rank, /notes, and /goals."""
from datetime import date


class TestRank:
    def test_requires_auth(self, client):
        assert client.get("/rank").status_code == 401

    def test_current_rank_is_latest_by_date_awarded(self, client, auth_headers):
        headers = auth_headers()
        assert client.get("/rank/current", headers=headers).status_code == 404

        client.post("/rank", headers=headers,
                    json={"belt": "blue", "stripes": 4, "date_awarded": "2023-01-01"})
        newest = client.post("/rank", headers=headers,
                             json={"belt": "purple", "stripes": 2, "date_awarded": "2025-06-01"})
        assert newest.status_code == 201

        current = client.get("/rank/current", headers=headers).json()
        assert current["belt"] == "purple"
        assert current["stripes"] == 2

        listed = client.get("/rank", headers=headers).json()
        assert [r["belt"] for r in listed] == ["purple", "blue"]

    def test_validation(self, client, auth_headers):
        headers = auth_headers()
        for bad in (
            {"belt": "red", "date_awarded": "2025-01-01"},
            {"belt": "blue", "stripes": 5, "date_awarded": "2025-01-01"},
            {"belt": "blue", "stripes": -1, "date_awarded": "2025-01-01"},
        ):
            assert client.post("/rank", headers=headers, json=bad).status_code == 422

    def test_update_delete_and_isolation(self, client, auth_headers):
        headers_a = auth_headers("a@example.com")
        headers_b = auth_headers("b@example.com")
        rank = client.post("/rank", headers=headers_a,
                           json={"belt": "blue", "stripes": 1,
                                 "date_awarded": str(date.today())}).json()
        rid = rank["rank_id"]

        assert client.put(f"/rank/{rid}", headers=headers_b,
                          json={"stripes": 3}).status_code == 404
        updated = client.put(f"/rank/{rid}", headers=headers_a, json={"stripes": 2})
        assert updated.json()["stripes"] == 2
        assert updated.json()["belt"] == "blue"

        assert client.delete(f"/rank/{rid}", headers=headers_b).status_code == 404
        assert client.delete(f"/rank/{rid}", headers=headers_a).status_code == 204
        assert client.get("/rank/current", headers=headers_a).status_code == 404


class TestNotes:
    def test_requires_auth(self, client):
        assert client.get("/notes").status_code == 401

    def test_create_and_defaults(self, client, auth_headers):
        headers = auth_headers()
        note = client.post("/notes", headers=headers,
                           json={"content": "elbow-knee connection"}).json()
        assert note["note_id"]
        assert note["title"] is None
        assert note["tags"] == []
        assert note["created_at"] and note["updated_at"]

    def test_content_is_required(self, client, auth_headers):
        response = client.post("/notes", headers=auth_headers(), json={"title": "x"})
        assert response.status_code == 422

    def test_search_matches_title_or_content(self, client, auth_headers):
        headers = auth_headers()
        client.post("/notes", headers=headers,
                    json={"title": "Guard ideas", "content": "play more lasso"})
        client.post("/notes", headers=headers,
                    json={"content": "watch the GUARD retention video"})
        client.post("/notes", headers=headers, json={"content": "unrelated"})

        found = client.get("/notes", headers=headers, params={"search": "guard"}).json()
        assert len(found) == 2

    def test_tag_filter(self, client, auth_headers):
        headers = auth_headers()
        client.post("/notes", headers=headers,
                    json={"content": "a", "tags": ["comp", "gi"]})
        client.post("/notes", headers=headers, json={"content": "b", "tags": ["gi"]})
        found = client.get("/notes", headers=headers, params={"tag": "comp"}).json()
        assert [n["content"] for n in found] == ["a"]

    def test_update_is_partial_and_bumps_updated_at(self, client, auth_headers):
        headers = auth_headers()
        note = client.post("/notes", headers=headers,
                           json={"title": "keep", "content": "original"}).json()
        updated = client.put(f"/notes/{note['note_id']}", headers=headers,
                             json={"content": "changed"}).json()
        assert updated["content"] == "changed"
        assert updated["title"] == "keep"
        assert updated["updated_at"] >= note["updated_at"]

    def test_isolation(self, client, auth_headers):
        headers_a = auth_headers("a@example.com")
        headers_b = auth_headers("b@example.com")
        note_b = client.post("/notes", headers=headers_b, json={"content": "mine"}).json()

        assert client.get("/notes", headers=headers_a).json() == []
        nid = note_b["note_id"]
        assert client.get(f"/notes/{nid}", headers=headers_a).status_code == 404
        assert client.put(f"/notes/{nid}", headers=headers_a,
                          json={"content": "stolen"}).status_code == 404
        assert client.delete(f"/notes/{nid}", headers=headers_a).status_code == 404
        assert client.delete(f"/notes/{nid}", headers=headers_b).status_code == 204


class TestGoals:
    def test_requires_auth(self, client):
        assert client.get("/goals").status_code == 401

    def test_create_defaults_private_and_active(self, client, auth_headers):
        goal = client.post("/goals", headers=auth_headers(),
                           json={"title": "Fix collar choke defense"}).json()
        assert goal["goal_id"]
        assert goal["status"] == "active"
        assert goal["visibility"] == "private"
        assert goal["target_date"] is None
        assert goal["owner_user_id"]

    def test_update_partial_and_isolation(self, client, auth_headers):
        headers_a = auth_headers("a@example.com")
        headers_b = auth_headers("b@example.com")
        goal = client.post("/goals", headers=headers_a,
                           json={"title": "T", "description": "keep"}).json()
        gid = goal["goal_id"]

        assert client.get("/goals", headers=headers_b).json() == []
        assert client.put(f"/goals/{gid}", headers=headers_b,
                          json={"status": "completed"}).status_code == 404

        updated = client.put(f"/goals/{gid}", headers=headers_a,
                             json={"status": "completed"}).json()
        assert updated["status"] == "completed"
        assert updated["description"] == "keep"

    def test_validation(self, client, auth_headers):
        headers = auth_headers()
        assert client.post("/goals", headers=headers,
                           json={"title": "x", "status": "someday"}).status_code == 422
        assert client.post("/goals", headers=headers,
                           json={"title": "x", "visibility": "public"}).status_code == 422

    def test_goals_have_no_delete_endpoint(self, client, auth_headers):
        headers = auth_headers()
        goal = client.post("/goals", headers=headers, json={"title": "T"}).json()
        response = client.delete(f"/goals/{goal['goal_id']}", headers=headers)
        assert response.status_code == 405
