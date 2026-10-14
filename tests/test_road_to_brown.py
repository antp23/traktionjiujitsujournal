"""Road to Brown Belt: hours since 2026-10-12 toward the 150h test."""


def _make(client, headers, **kw):
    payload = {"session_type": "gi", "duration_minutes": 60}
    payload.update(kw)
    r = client.post("/sessions", headers=headers, json=payload)
    assert r.status_code == 201, r.text


def test_requires_auth(client):
    assert client.get("/sessions/stats/road-to-brown").status_code == 401


def test_counts_attended_since_start(client, auth_headers):
    h = auth_headers()
    _make(client, h, date="2026-10-11", duration_minutes=120)  # before start
    _make(client, h, date="2026-10-12", duration_minutes=60)
    _make(client, h, date="2026-10-13", duration_minutes=90)
    _make(client, h, date="2026-10-14", duration_minutes=60, attended=False)
    data = client.get("/sessions/stats/road-to-brown", headers=h,
                      params={"today": "2026-10-14"}).json()
    assert data["hours_logged"] == 2.5
    assert data["next_milestone"]["label"] == "4th stripe"
    assert data["hours_to_next_milestone"] == 72.5
    assert data["hours_remaining"] == 147.5
    assert data["four_week_avg_pace"] == 0.62 or data["four_week_avg_pace"] == 0.63
    weeks = (193) / 7  # 2026-10-14 -> 2027-04-25
    assert abs(data["weekly_pace_needed"] - 147.5 / weeks) < 0.01
    assert [m["reached"] for m in data["milestones"]] == [False, False]


def test_past_first_milestone(client, auth_headers):
    h = auth_headers()
    for day in range(1, 27):
        _make(client, h, date=f"2026-11-{day:02d}", duration_minutes=180)
    data = client.get("/sessions/stats/road-to-brown", headers=h,
                      params={"today": "2026-12-01"}).json()
    assert data["hours_logged"] == 78
    assert data["milestones"][0]["reached"] is True
    assert data["next_milestone"]["label"] == "Brown belt test"
    assert data["hours_to_next_milestone"] == 72
