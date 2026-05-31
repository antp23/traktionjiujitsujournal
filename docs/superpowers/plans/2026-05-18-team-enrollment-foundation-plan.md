# Team Enrollment Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first team V1 slice: local magic-link-style auth, gym workspace invites, athlete profile onboarding, private-by-default ownership fields, and opt-in note/goal sharing foundations.

**Architecture:** Keep the app local-first and SQLite-backed. Add explicit team/account models to the existing SQLAlchemy schema and expose simple FastAPI routes that the React app can consume. The first implementation may use dev-friendly token return values instead of outbound email, but the API shape should make replacing it with real email delivery straightforward.

**Tech Stack:** FastAPI, SQLAlchemy, SQLite, Pydantic v2, React, Vite, Tailwind, existing axios API wrapper.

---

## Work Boundaries

Backend worker owns:

- `backend/models.py`
- `backend/schemas.py`
- `backend/main.py`
- `backend/routers/auth.py`
- `backend/routers/workspaces.py`
- `backend/routers/sharing.py`
- backend-focused tests under `tests/`

Frontend worker owns:

- `frontend/src/api.js`
- `frontend/src/App.jsx`
- `frontend/src/components/Layout.jsx`
- new frontend pages/components under `frontend/src/pages/` and `frontend/src/components/`
- frontend styles if needed

Coordinator owns:

- plan/spec docs
- final integration checks
- conflict resolution

Do not modify coach assignment, curriculum, class-planning, or public team-feed features.

## API Contract For V1 Slice

### Auth

`POST /auth/request-link`

Request:

```json
{ "email": "athlete@example.com" }
```

Response:

```json
{
  "message": "Magic link created.",
  "dev_token": "token-visible-in-dev"
}
```

`POST /auth/consume-link`

Request:

```json
{ "token": "token-visible-in-dev" }
```

Response:

```json
{
  "session_token": "local-session-token",
  "user": {
    "user_id": "uuid",
    "email": "athlete@example.com",
    "name": null,
    "preferred_name": null
  }
}
```

`GET /auth/me`

Header: `x-session-token: local-session-token`

Response:

```json
{
  "user": { "user_id": "uuid", "email": "athlete@example.com", "name": null, "preferred_name": null },
  "memberships": [],
  "profile": null
}
```

### Workspace Invite And Enrollment

`POST /workspaces/bootstrap`

Creates the first local gym workspace and owner if none exists. This is a local bootstrap endpoint for this personal/semi-internal app.

Request:

```json
{
  "gym_name": "Traktion Jiujitsu Academy",
  "owner_email": "owner@example.com",
  "owner_name": "Anthony"
}
```

Response includes workspace, owner, membership, and an invite code.

`GET /workspaces/invites/{code}`

Public endpoint used by join screen. Returns gym name and whether invite is usable.

`POST /workspaces/join`

Header: `x-session-token`

Request:

```json
{ "invite_code": "abc123" }
```

Response: membership with role `athlete`.

`PUT /workspaces/profile`

Header: `x-session-token`

Request:

```json
{
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
  "injuries_or_limitations": "left shoulder"
}
```

Response: updated user, athlete profile, and WhatsApp identity.

### Goals And Sharing

`GET /goals`, `POST /goals`, `PUT /goals/{goal_id}`

Goals are private by default. Goal fields: `title`, `description`, `status`, `visibility`, `target_date`.

`POST /sharing/threads`

Header: `x-session-token`

Request:

```json
{
  "source_type": "goal",
  "source_id": "uuid",
  "body": "Can you look at this?"
}
```

Response: thread and initial message.

`GET /sharing/inbox`

Header: `x-session-token`

For coaches/owners, returns shared threads in their workspace. For athletes, returns their own threads.

`POST /sharing/threads/{thread_id}/messages`

Header: `x-session-token`

Request:

```json
{ "body": "Frame first, then recover knee line." }
```

`POST /sharing/messages/{message_id}/pin`

Header: `x-session-token`

Creates a CoachNote from a message.

## Backend Tasks

### Task 1: Add Team/Auth Models And Schemas

**Files:**
- Modify: `backend/models.py`
- Modify: `backend/schemas.py`
- Test: `tests/test_team_foundation.py`

- [ ] Add SQLAlchemy models: `User`, `AuthToken`, `GymWorkspace`, `Membership`, `InviteLink`, `AthleteProfile`, `WhatsAppIdentity`, `Goal`, `ShareThread`, `ThreadMessage`, `CoachNote`.
- [ ] Add owner fields where needed without breaking old data: `owner_user_id` nullable on existing personal tables may be deferred except for `Note` and `Goal`.
- [ ] Add Pydantic request/response schemas for auth, workspace, profile, goals, sharing, and coach notes.
- [ ] Add unit tests that create an in-memory SQLite database, call `Base.metadata.create_all`, and assert the new tables exist.

### Task 2: Implement Auth And Workspace Enrollment Routes

**Files:**
- Create: `backend/routers/auth.py`
- Create: `backend/routers/workspaces.py`
- Modify: `backend/main.py`
- Test: `tests/test_team_foundation.py`

- [ ] Implement `get_current_user` dependency using `x-session-token`.
- [ ] Implement `POST /auth/request-link`, `POST /auth/consume-link`, and `GET /auth/me`.
- [ ] Implement `POST /workspaces/bootstrap`, `GET /workspaces/invites/{code}`, `POST /workspaces/join`, and `PUT /workspaces/profile`.
- [ ] Include the new routers in `backend/main.py`.
- [ ] Add tests for request-link/consume-link/me, bootstrap invite creation, invite lookup, join, and profile update.

### Task 3: Implement Goals And Sharing Routes

**Files:**
- Create: `backend/routers/goals.py`
- Create: `backend/routers/sharing.py`
- Modify: `backend/main.py`
- Test: `tests/test_team_foundation.py`

- [ ] Implement private-by-default goal CRUD for the current user.
- [ ] Implement share thread creation for a goal or note owned by the current user.
- [ ] Implement shared inbox role behavior: athletes see own threads; owner/coach memberships see workspace shared threads.
- [ ] Implement thread messages.
- [ ] Implement pin-to-CoachNote.
- [ ] Add tests for private goals, shared thread creation, coach inbox visibility, reply, and pin.

## Frontend Tasks

### Task 4: Add Client Auth State And Enrollment API

**Files:**
- Modify: `frontend/src/api.js`
- Create: `frontend/src/auth.js`
- Modify: `frontend/src/App.jsx`

- [ ] Add API helpers for auth, workspace invite lookup, join, profile update, goals, and sharing.
- [ ] Store `session_token` in localStorage.
- [ ] Include `x-session-token` on API requests when present.
- [ ] Add route guards for app pages: unauthenticated users land on login/join flow, authenticated users can use the app.

### Task 5: Build Login, Join, And Profile Onboarding Screens

**Files:**
- Create: `frontend/src/pages/Login.jsx`
- Create: `frontend/src/pages/JoinWorkspace.jsx`
- Create: `frontend/src/pages/Onboarding.jsx`
- Modify: `frontend/src/App.jsx`

- [ ] Login screen requests a magic link and shows `dev_token` for local use.
- [ ] Consume-link flow accepts a token and stores session.
- [ ] Join screen accepts invite code from URL or input and calls join endpoint.
- [ ] Onboarding screen captures student details, including optional WhatsApp phone.
- [ ] On successful onboarding, route to dashboard.

### Task 6: Build Goals And Share-With-Coach UI

**Files:**
- Create: `frontend/src/pages/Goals.jsx`
- Create: `frontend/src/pages/SharedInbox.jsx`
- Modify: `frontend/src/components/Layout.jsx`
- Modify: `frontend/src/App.jsx`
- Modify: `frontend/src/pages/Notes.jsx`

- [ ] Add Goals page with private goal list and create form.
- [ ] Add "Ask coach" on goals.
- [ ] Add "Ask coach" on notes.
- [ ] Add Shared Inbox page showing threads and messages.
- [ ] Add pin action for coach replies if available in the API.
- [ ] Add navigation entries for Goals and Shared Inbox.

## Verification

Run these commands after integration:

```bash
/Users/anthonypaquin/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m unittest tests/test_contracts.py tests/test_team_foundation.py
cd frontend
/Users/anthonypaquin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node ./node_modules/eslint/bin/eslint.js .
/Users/anthonypaquin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node ./node_modules/vite/bin/vite.js build
```

Browser smoke:

- Open `http://127.0.0.1:5173/`.
- Request a login token.
- Consume token.
- Join a workspace by invite code.
- Complete profile.
- Create a goal.
- Share it with coach.

## Self-Review Notes

This plan intentionally implements only the team enrollment and sharing foundation. It does not implement full Coach's Brief intelligence, team curriculum, class planning, coach assignment workflows, or production email delivery.
