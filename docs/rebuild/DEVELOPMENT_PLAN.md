# BJJ Tracker v2 — Rebuild Development Plan

Date: 2026-07-09
Status: executed on branch `claude/app-last-update-timeline-nlo5p3`

## 1. Premise

The v1 codebase (last touched 2026-05-31) is the **behavioral specification**. The rebuild
does not change what the product does — it changes how well the code that does it is built.
The contract that must survive unchanged:

1. **The HTTP API** — every route, method, status code, response shape, auth rule, and quirk.
2. **The SQLite schema** — the production database on Render (`/var/lib/bjj-tracker/bjj.db`)
   must keep working with zero data migration.
3. **The deploy surface** — `render.yaml` runs `uvicorn main:app` from `backend/`; all
   `BJJ_*` environment variables keep their meaning.
4. **The UI routes and flows** — login → join → onboarding → journal, and every page's
   interaction with the API.

## 2. Method: characterization tests first

The order of operations is the core of this plan:

1. **Write a characterization test suite against v1** (`tests/`). It encodes what the app
   *actually does* — including warts (see §5). ~130 assertions-worth of coverage across auth,
   ownership/privacy, CRUD, stats math, quick-log parsing, workspaces, sharing, webhooks,
   and middleware.
2. **Run the suite against the v1 backend until it is fully green.** A red test at this stage
   means the *test* is wrong, not the app. This validates that the suite is a faithful spec.
3. **Delete v1 backend code, build v2 from scratch, and loop the suite until green.**
   A red test now means the *rebuild* is wrong.
4. Frontend gates: `npm run lint` + `npm run build` + source-contract tests (field-name
   checks that pin the API↔UI coupling), since v1 has no UI test harness to inherit.

The three legacy test files (`test_contracts.py`, `test_privacy_hardening.py`,
`test_team_foundation.py`) are absorbed into the new suite — every assertion they made is
preserved or strengthened — and the originals are removed.

## 3. What "10x better" means here (backend)

v1 is a single flat layer: 14 router files that each do HTTP parsing, auth, business logic,
SQL, and serialization inline, plus import-time side effects (the `coaches` router creates
tables at import; `oura` builds its own DB sessions by hand; `main.py` carries a 80-line
inline SQLite migration).

v2 architecture (`backend/app/`):

```
backend/
  main.py               # uvicorn entrypoint shim → app.main:app (keeps render.yaml working)
  database.py, models.py, schemas.py   # thin re-export shims (test/tooling compatibility)
  app/
    config.py           # every env var read in ONE place, typed accessors
    db.py               # engine/session factory, no import-time file I/O surprises
    models.py           # all ORM models (incl. Coach), owner indexes
    schemas.py          # all Pydantic contracts
    migrations.py       # the idempotent SQLite column back-fills, isolated + tested
    security.py         # magic links, session tokens, throttling, SMTP delivery
    services/
      stats.py          # session stats (streak math) + roll stats — pure, unit-testable
      quicklog.py       # the /parse NLP heuristics — pure functions + one DB writer
    api/
      deps.py           # get_db / get_current_user dependencies
      auth.py sessions.py techniques.py rolls.py rank.py notes.py coaches.py
      goals.py workspaces.py sharing.py parse.py dashboard.py oura.py whatsapp.py
    main.py             # create_app(): CORS, API-key middleware, router registry, startup
```

Concrete improvements, none contract-breaking:

- **Layering** — routers only translate HTTP↔domain; stats/parse logic is pure and unit-tested
  directly, not just through HTTP.
- **No import-time side effects** — table creation and column migrations happen once, at
  startup, from one place.
- **Configuration** — one `config.py` instead of ~30 scattered `os.getenv` calls; every knob
  documented and read consistently (bool/int parsing unified).
- **Dashboard reuses services** — v1's `/dashboard` re-implemented spotlight selection and
  imported private helpers from routers; v2 composes the same service functions the individual
  endpoints use, so the numbers cannot drift apart.
- **Ownership scoping as a helper** — the `owner_user_id == current_user` + 404 pattern is one
  function, not 30 hand-copies.
- **Indexes** on all `owner_user_id` columns and `sessions.date` (create_all only; additive,
  no-op risk-free on the existing production file).
- **Timing-safe API-key comparison** in the middleware (v1 used `!=`).
- **Type hints + docstrings throughout**; `httpx` timeout/error translation for Oura kept and
  centralized.
- **Test infrastructure** — a proper pytest suite with a shared fixture harness replaces
  three ad-hoc unittest files with copy-pasted setup.

## 4. What "10x better" means here (frontend)

The v1 frontend is functionally fine but structurally ad-hoc: axios calls duplicated per page,
inconsistent error handling (several pages swallow failures silently), a mix of three styling
dialects (raw Tailwind, `journal-*` CSS classes, inline `style=`), an unused `StatCard`
component, and a hardcoded `http://localhost:8000/oura/auth` link that breaks the Recovery
page in production.

v2 keeps React + Vite + Tailwind and every route/flow, and restructures:

- `src/lib/api.js` — single typed client; every endpoint in one place; consistent error
  normalization (`apiErrorMessage(err, fallback)`) so pages stop inventing their own.
- `src/lib/auth.jsx` — the session context, now a real `.jsx` module (v1 used
  `createElement` to dodge its own file extension), plus logout that actually calls
  `POST /auth/logout` to revoke the server-side session (v1 only cleared localStorage).
- `src/hooks/useAsyncData.js` — one loading/error/reload hook replacing the
  copy-pasted `useState(loading)` + `useEffect` block in every page.
- Oura connect link built from `VITE_API_URL` instead of hardcoded localhost.
- Dead code removed (`StatCard`, unused imports); ESLint clean, production build green.
- Visual/UX parity otherwise — the redesign of individual screens is *deliberately* out of
  scope until an E2E harness exists (see §7).

## 5. Preserved quirks (deliberate)

Characterization means keeping behavior that a green-field design would change. These are
pinned by tests and kept in v2, flagged here so a future release can change them consciously:

| Quirk | Where | Why kept |
|---|---|---|
| `/coaches` CRUD requires no authentication and is globally shared | coaches router | v1 contract; contains only coach names/gyms. Fix queued for v2.1 with auth + ownership. |
| `/oura/*` (status, data, sync) has no per-user auth; Oura tokens are a global singleton | oura router | Single-athlete feature in v1. v2.1 should bind to user. |
| Goals have no DELETE endpoint (archive via status instead) | goals router | UI never deletes goals. |
| `POST /workspaces/bootstrap` is unauthenticated and idempotently returns the single existing workspace | workspaces router | Launch-time single-gym design. |
| Roll outcomes accept legacy values `win`, `loss`, `competitive`; techniques accept `no_gi` | schemas | Legacy seed data must keep serializing. |
| Roll stats count only `submission_*`/`points_*` as W/L; legacy `win`/`loss` land in `draws` bucket in per-partner stats and are excluded from top-level wins/losses | stats service | Exact v1 math, pinned by tests. |
| `PUT /coaches/{id}` uses `exclude_none` (cannot null a field); all other PUTs use `exclude_unset` | coaches router | v1 contract. |
| Quick-log always defaults `gym_location` to "Traktion Jiu Jitsu Academy" and session type to `gi` | quicklog service | v1 behavior, pinned. |
| Sharing a note claims legacy unowned notes (`owner_user_id IS NULL`) for the sharer | sharing router | Data back-fill path from pre-auth era. |
| `x-api-key` middleware effectively guards only `/oura/*` (everything else is in the session-auth prefix list or public) | main app | v1 behavior; session auth is the real boundary. |

## 6. Test suite map (`tests/`)

- `conftest.py` — in-memory SQLite + dependency override + `client` / `session_for` fixtures;
  env-var isolation per test.
- `test_auth.py` — magic-link request (503 unconfigured / dev token / SMTP send + 502 failure),
  consume (single-use, expiry), sessions (expiry, logout revocation, bad token), throttling
  (per-email, case-insensitive, window), `/auth/me`.
- `test_sessions.py` — CRUD, filters (type/location/date range/limit), validation bounds
  (duration 1–480, energy 1–10, rounds 0–100), stats math including weekly-streak edge cases
  and 30/90-day rates, partial updates.
- `test_techniques.py` — CRUD, spotlight preference (learning/drilling first, fallback, 404),
  filters (category, position ilike, gi_nogi, proficiency, tag, search, sort), links
  (create/duplicate-delete quirk/unlink), legacy `no_gi`.
- `test_rolls.py` — CRUD gated on owned session (404 cross-user), stats: W/L/draw math,
  win_rate rounding, top-5 counters, partner breakdown incl. legacy-outcome bucketing.
- `test_rank_notes_goals.py` — rank CRUD + `/rank/current` ordering; notes CRUD + search
  (title OR content, ilike) + tag filter; goals create/list/update, defaults, no-delete.
- `test_workspaces_sharing.py` — bootstrap idempotency, invite lookup, join (idempotent,
  reactivation), profile upsert + WhatsApp identity, thread creation (goal flips to shared,
  note claiming), inbox visibility (coach vs athlete vs stranger), replies, pin idempotency.
- `test_parse.py` — intent classification, date phrases (yesterday, last weekday, "Apr 2",
  "4/2"), durations (hours/minutes/word), energy words, focus/notes extraction, technique
  dedupe, note prefix stripping, unknown → raw capture; exact response `action`s and data keys.
- `test_dashboard.py` — full payload shape, per-user scoping, empty-state defaults.
- `test_whatsapp.py` — feature flag off → 404, challenge verification, signature enforcement,
  happy path → note, dedupe, unmatched phone.
- `test_coaches_oura_infra.py` — coaches CRUD (unauthenticated), `/health`, CORS env,
  API-key middleware behavior, `/oura/status`+`/oura/data`, SQLite column back-fill migration.
- `test_frontend_contract.py` — pins the API field names the UI reads (absorbs v1's
  source-contract test, extended to the new lib/api layer).

## 7. Explicit non-goals / deferred (v2.1+ backlog)

- Postgres migration (env hook `BJJ_DATABASE_URL` already works; needs Alembic + data move).
- Auth + per-user scoping for `/coaches` and `/oura` (contract change — needs a deprecation pass).
- Hashing session tokens at rest; CSRF-hardened cookie sessions.
- Frontend E2E harness (Playwright) — prerequisite for any real UI redesign.
- WhatsApp capture GA (feature-flagged code retained as-is).
- Achievements/badges (Progress page placeholder retained).

## 8. Acceptance criteria

1. Characterization suite green against v1 **before** any v1 code is deleted (recorded in
   the commit history: tests land first, green, on the unmodified v1 backend).
2. Same suite green against v2 with zero test edits (the suite is the contract).
3. `npm run lint` and `npm run build` green on the rebuilt frontend.
4. `render.yaml`, `start.sh`, and all env vars work unchanged.
