"""Characterization: workspace bootstrap/join/profile and coach sharing."""


def _join(client, headers, code):
    response = client.post("/workspaces/join", headers=headers, json={"invite_code": code})
    assert response.status_code == 200, response.text
    return response.json()


class TestBootstrap:
    def test_bootstrap_creates_owner_membership_and_invite(self, client, bootstrap_workspace):
        payload = bootstrap_workspace()
        assert payload["workspace"]["gym_name"] == "Traktion Jiujitsu Academy"
        assert payload["owner"]["email"] == "owner@example.com"
        assert payload["owner"]["name"] == "Anthony"
        assert payload["membership"]["role"] == "owner"
        assert payload["membership"]["status"] == "active"
        assert payload["invite"]["code"]
        assert payload["invite"]["active"] is True

    def test_bootstrap_is_idempotent_single_workspace(self, client, bootstrap_workspace):
        first = bootstrap_workspace()
        second = bootstrap_workspace(gym_name="Another Gym Name")
        # The single existing workspace wins regardless of the new name.
        assert second["workspace"]["workspace_id"] == first["workspace"]["workspace_id"]
        assert second["workspace"]["gym_name"] == "Traktion Jiujitsu Academy"
        assert second["invite"]["code"] == first["invite"]["code"]
        assert second["membership"]["membership_id"] == first["membership"]["membership_id"]

    def test_bootstrap_normalizes_owner_email(self, client, bootstrap_workspace):
        payload = bootstrap_workspace(owner_email="  Owner@Example.COM ")
        assert payload["owner"]["email"] == "owner@example.com"


class TestInvites:
    def test_lookup(self, client, bootstrap_workspace):
        code = bootstrap_workspace()["invite"]["code"]
        found = client.get(f"/workspaces/invites/{code}")
        assert found.status_code == 200
        assert found.json() == {"gym_name": "Traktion Jiujitsu Academy", "usable": True}
        assert client.get("/workspaces/invites/bogus").status_code == 404


class TestJoinAndCurrent:
    def test_join_flow(self, client, bootstrap_workspace, auth_headers):
        code = bootstrap_workspace()["invite"]["code"]
        headers = auth_headers("athlete@example.com")

        membership = _join(client, headers, code)
        assert membership["role"] == "athlete"
        assert membership["status"] == "active"

        # Idempotent re-join returns the same membership.
        again = _join(client, headers, code)
        assert again["membership_id"] == membership["membership_id"]

        current = client.get("/workspaces/current", headers=headers).json()
        assert current["workspace"]["gym_name"] == "Traktion Jiujitsu Academy"
        assert current["membership"]["role"] == "athlete"
        assert current["invite"] is None  # athletes never see the invite

    def test_join_requires_valid_code(self, client, auth_headers):
        response = client.post("/workspaces/join", headers=auth_headers(),
                               json={"invite_code": "bogus"})
        assert response.status_code == 404

    def test_join_requires_auth(self, client, bootstrap_workspace):
        code = bootstrap_workspace()["invite"]["code"]
        assert client.post("/workspaces/join", json={"invite_code": code}).status_code == 401

    def test_current_without_membership(self, client, auth_headers):
        current = client.get("/workspaces/current", headers=auth_headers()).json()
        assert current == {"workspace": None, "membership": None, "invite": None}

    def test_owner_sees_invite(self, client, bootstrap_workspace, session_for):
        bootstrap_workspace(owner_email="owner@example.com")
        headers = {"x-session-token": session_for("owner@example.com")}
        current = client.get("/workspaces/current", headers=headers).json()
        assert current["membership"]["role"] == "owner"
        assert current["invite"]["code"]


class TestProfile:
    PROFILE = {
        "name": "Student Name",
        "preferred_name": "Student",
        "whatsapp_phone": "+15555555555",
        "belt": "blue",
        "stripes": 1,
        "years_training": 2,
        "typical_training_frequency": "3x/week",
        "gi_nogi_preference": "both",
        "competition_interest": "maybe",
        "current_focus": "guard retention",
        "favorite_positions": ["De La Riva"],
        "problem_positions": ["bottom half"],
        "injuries_or_limitations": "left shoulder",
    }

    def test_profile_upsert_and_whatsapp_identity(self, client, auth_headers):
        headers = auth_headers("athlete@example.com")
        response = client.put("/workspaces/profile", headers=headers, json=self.PROFILE)
        assert response.status_code == 200
        payload = response.json()
        assert payload["user"]["name"] == "Student Name"
        assert payload["user"]["preferred_name"] == "Student"
        assert payload["profile"]["belt"] == "blue"
        assert payload["profile"]["favorite_positions"] == ["De La Riva"]
        assert payload["whatsapp_identity"]["phone"] == "+15555555555"

        me = client.get("/auth/me", headers=headers).json()
        assert me["profile"]["belt"] == "blue"

        # Second update replaces fields and re-points the identity.
        updated = client.put("/workspaces/profile", headers=headers,
                             json={**self.PROFILE, "belt": "purple",
                                   "whatsapp_phone": "+16666666666"}).json()
        assert updated["profile"]["belt"] == "purple"
        assert updated["whatsapp_identity"]["phone"] == "+16666666666"

    def test_profile_without_phone_creates_no_identity(self, client, auth_headers):
        headers = auth_headers()
        response = client.put("/workspaces/profile", headers=headers,
                              json={"name": "Solo", "preferred_name": None})
        assert response.status_code == 200
        assert response.json()["whatsapp_identity"] is None

    def test_profile_requires_auth_and_name(self, client, auth_headers):
        assert client.put("/workspaces/profile", json={"name": "X"}).status_code == 401
        assert client.put("/workspaces/profile", headers=auth_headers(),
                          json={"preferred_name": "X"}).status_code == 422


class TestSharing:
    def _enrolled_athlete(self, client, bootstrap_workspace, session_for, email):
        code = bootstrap_workspace()["invite"]["code"]
        headers = {"x-session-token": session_for(email)}
        _join(client, headers, code)
        return headers

    def test_sharing_requires_membership(self, client, auth_headers):
        headers = auth_headers()
        goal = client.post("/goals", headers=headers, json={"title": "T"}).json()
        response = client.post("/sharing/threads", headers=headers,
                               json={"source_type": "goal",
                                     "source_id": goal["goal_id"], "body": "look"})
        assert response.status_code == 400
        assert response.json()["detail"] == "Join a workspace before sharing"

    def test_sharing_goal_flips_visibility_and_notifies_coach(
        self, client, bootstrap_workspace, session_for
    ):
        athlete = self._enrolled_athlete(client, bootstrap_workspace, session_for,
                                         "athlete@example.com")
        owner = {"x-session-token": session_for("owner@example.com")}
        stranger = self._enrolled_athlete(client, bootstrap_workspace, session_for,
                                          "other@example.com")

        goal = client.post("/goals", headers=athlete, json={"title": "Escape mount"}).json()
        assert goal["visibility"] == "private"

        created = client.post("/sharing/threads", headers=athlete,
                              json={"source_type": "goal", "source_id": goal["goal_id"],
                                    "body": "Can you look at this?"})
        assert created.status_code == 201
        thread = created.json()["thread"]
        first_message = created.json()["initial_message"]
        assert thread["source_type"] == "goal"
        assert thread["status"] == "open"
        assert first_message["body"] == "Can you look at this?"

        shared_goal = client.get("/goals", headers=athlete).json()[0]
        assert shared_goal["visibility"] == "shared"

        # Owner inbox sees the thread with its messages; a fellow athlete does not.
        owner_inbox = client.get("/sharing/inbox", headers=owner).json()
        assert [t["thread_id"] for t in owner_inbox] == [thread["thread_id"]]
        assert [m["body"] for m in owner_inbox[0]["messages"]] == ["Can you look at this?"]
        assert client.get("/sharing/inbox", headers=stranger).json() == []

        athlete_inbox = client.get("/sharing/inbox", headers=athlete).json()
        assert len(athlete_inbox) == 1

    def test_cannot_share_foreign_goal_or_note(self, client, bootstrap_workspace, session_for):
        athlete = self._enrolled_athlete(client, bootstrap_workspace, session_for,
                                         "athlete@example.com")
        other = self._enrolled_athlete(client, bootstrap_workspace, session_for,
                                       "other@example.com")
        goal = client.post("/goals", headers=other, json={"title": "Theirs"}).json()
        note = client.post("/notes", headers=other, json={"content": "theirs"}).json()

        for source_type, source_id in (("goal", goal["goal_id"]), ("note", note["note_id"])):
            response = client.post("/sharing/threads", headers=athlete,
                                   json={"source_type": source_type,
                                         "source_id": source_id, "body": "x"})
            assert response.status_code == 404

    def test_replies_and_pinning(self, client, bootstrap_workspace, session_for):
        athlete = self._enrolled_athlete(client, bootstrap_workspace, session_for,
                                         "athlete@example.com")
        owner = {"x-session-token": session_for("owner@example.com")}
        stranger = self._enrolled_athlete(client, bootstrap_workspace, session_for,
                                          "other@example.com")

        note = client.post("/notes", headers=athlete, json={"content": "half guard woes"}).json()
        thread = client.post("/sharing/threads", headers=athlete,
                             json={"source_type": "note", "source_id": note["note_id"],
                                   "body": "thoughts?"}).json()["thread"]
        tid = thread["thread_id"]

        # A non-coach workspace member cannot post into someone else's thread.
        assert client.post(f"/sharing/threads/{tid}/messages", headers=stranger,
                           json={"body": "sneaky"}).status_code == 404

        reply = client.post(f"/sharing/threads/{tid}/messages", headers=owner,
                            json={"body": "Frame first, then recover knee line."})
        assert reply.status_code == 201
        message_id = reply.json()["message_id"]

        pinned = client.post(f"/sharing/messages/{message_id}/pin", headers=owner)
        assert pinned.status_code == 201
        coach_note = pinned.json()
        assert coach_note["content"] == "Frame first, then recover knee line."
        assert coach_note["source"] == "coach"
        assert coach_note["source_message_id"] == message_id

        # Pinning again returns the same coach note.
        again = client.post(f"/sharing/messages/{message_id}/pin", headers=owner)
        assert again.status_code == 201
        assert again.json()["coach_note_id"] == coach_note["coach_note_id"]

        assert client.post(f"/sharing/messages/{message_id}/pin",
                           headers=stranger).status_code == 404

    def test_thread_message_on_unknown_thread(self, client, auth_headers):
        response = client.post("/sharing/threads/nope/messages", headers=auth_headers(),
                               json={"body": "x"})
        assert response.status_code == 404
