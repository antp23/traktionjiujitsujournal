"""Personal API access keys and the session date-update fix."""
import hashlib

import models


def _create_key(client, headers, name="Grok Bot"):
    response = client.post("/auth/api-keys", headers=headers, json={"name": name})
    assert response.status_code == 201, response.text
    return response.json()


class TestApiKeys:
    def test_create_list_revoke(self, client, auth_headers, db):
        headers = auth_headers()
        created = _create_key(client, headers)
        raw = created["api_key"]
        assert raw.startswith("bjj_") and len(raw) > 40
        assert created["name"] == "Grok Bot"
        assert created["key_prefix"] == raw[:10]

        stored = db.query(models.ApiKey).one()
        assert stored.key_hash == hashlib.sha256(raw.encode()).hexdigest()
        assert raw not in (stored.key_hash, stored.key_prefix)

        listed = client.get("/auth/api-keys", headers=headers).json()
        assert [k["key_id"] for k in listed] == [created["key_id"]]
        assert "api_key" not in listed[0] and "key_hash" not in listed[0]

        assert client.delete(f"/auth/api-keys/{created['key_id']}", headers=headers).status_code == 200
        assert client.get("/auth/api-keys", headers=headers).json() == []
        assert client.delete(f"/auth/api-keys/{created['key_id']}", headers=headers).status_code == 404

    def test_key_authenticates_and_revoked_key_rejected(self, client, auth_headers):
        headers = auth_headers()
        created = _create_key(client, headers)
        bearer = {"Authorization": f"Bearer {created['api_key']}"}

        me = client.get("/auth/me", headers=bearer)
        assert me.status_code == 200
        assert me.json()["user"]["email"] == "athlete@example.com"
        assert client.get("/sessions", headers={"x-session-token": created["api_key"]}).status_code == 200
        post = client.post("/sessions", headers=bearer,
                           json={"date": "2026-10-10", "session_type": "gi"})
        assert post.status_code == 201

        listed = client.get("/auth/api-keys", headers=headers).json()
        assert listed[0]["last_used_at"] is not None

        client.delete(f"/auth/api-keys/{created['key_id']}", headers=headers)
        assert client.get("/sessions", headers=bearer).status_code == 401

    def test_invalid_key_rejected(self, client):
        assert client.get("/sessions", headers={"Authorization": "Bearer bjj_nope"}).status_code == 401

    def test_api_key_cannot_manage_keys(self, client, auth_headers):
        created = _create_key(client, auth_headers())
        bearer = {"Authorization": f"Bearer {created['api_key']}"}
        assert client.get("/auth/api-keys", headers=bearer).status_code == 401
        assert client.post("/auth/api-keys", headers=bearer, json={"name": "x"}).status_code == 401
        assert client.delete(f"/auth/api-keys/{created['key_id']}", headers=bearer).status_code == 401

    def test_keys_scoped_to_owner(self, client, auth_headers):
        created = _create_key(client, auth_headers("a@example.com"))
        other = auth_headers("b@example.com")
        assert client.get("/auth/api-keys", headers=other).json() == []
        assert client.delete(f"/auth/api-keys/{created['key_id']}", headers=other).status_code == 404

    def test_requires_session(self, client):
        assert client.get("/auth/api-keys").status_code == 401
        assert client.post("/auth/api-keys", json={"name": "x"}).status_code == 401


class TestSessionDateUpdate:
    def test_put_changes_date(self, client, auth_headers):
        headers = auth_headers()
        created = client.post("/sessions", headers=headers,
                              json={"date": "2026-07-28", "session_type": "gi"}).json()
        response = client.put(f"/sessions/{created['session_id']}", headers=headers,
                              json={"date": "2026-07-27"})
        assert response.status_code == 200, response.text
        assert response.json()["date"] == "2026-07-27"
