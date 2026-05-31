# Launch Finish Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Finish the minimum safe launch scope for the BJJ team journal without WhatsApp capture.

**Architecture:** Keep the current FastAPI, SQLAlchemy, SQLite, React, and Vite stack. Harden the existing product instead of adding new product surfaces: user-scope personal data, make auth less fragile, keep WhatsApp capture disabled, document deployment, and verify the launch paths.

**Tech Stack:** FastAPI, SQLAlchemy, SQLite, Pydantic v2, React, Vite, Tailwind, unittest, ESLint.

---

## Launch Scope

In:

- Team workspace, self-enrollment, profile onboarding.
- Private athlete journal data.
- Goals and explicit coach sharing.
- Coach inbox.
- Optional WhatsApp phone as contact/profile detail.

Out:

- WhatsApp capture.
- Billing.
- Class scheduling.
- Gym CRM.
- Automatic coach access to private athlete journals.

## Workstreams

### Task 1: Backend Privacy

Owner: backend privacy worker.

- [ ] Require authenticated user on personal journal routes.
- [ ] Scope notes, sessions, techniques, rolls, rank logs, dashboard, and parser writes by `owner_user_id`.
- [ ] Remove ownership assignment during sharing for unowned notes.
- [ ] Add tests proving Athlete A cannot see or mutate Athlete B data.

### Task 2: Auth Hardening

Owner: auth worker.

- [ ] Add token expiration for magic links and sessions.
- [ ] Add logout/session revocation.
- [ ] Gate dev token visibility behind an explicit env flag.
- [ ] Add tests for expired, consumed, and revoked tokens.

### Task 3: Frontend Launch UX

Owner: frontend worker.

- [ ] Ensure empty states help a new athlete start logging.
- [ ] Ensure share/private states are clear.
- [ ] Ensure WhatsApp is shown only as optional contact/profile detail.
- [ ] Keep the existing quiet mat-journal visual direction.

### Task 4: Deployment Readiness

Owner: deployment worker/coordinator.

- [ ] Document required env vars.
- [ ] Document backup/restore and database caveats.
- [ ] Document launch smoke tests.
- [ ] Keep `BJJ_ENABLE_WHATSAPP_CAPTURE` unset for go-live.

### Task 5: Verification

Owner: coordinator.

- [ ] Run backend tests.
- [ ] Run frontend lint.
- [ ] Run frontend production build.
- [ ] Start local backend/frontend.
- [ ] Smoke test login, workspace, onboarding, dashboard, journal, goals, sharing, and coach inbox.

## Launch Bar

- Athlete A cannot see Athlete B journal data.
- Coach sees only explicitly shared items.
- Magic links expire and cannot be reused.
- Logout invalidates the current session.
- New athlete can join, onboard, and create first useful journal record.
- WhatsApp capture endpoints stay disabled unless explicitly enabled.
- README/runbook can be followed by future-you without chat history.
