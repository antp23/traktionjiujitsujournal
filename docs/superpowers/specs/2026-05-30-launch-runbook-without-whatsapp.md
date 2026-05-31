# Launch Runbook Without WhatsApp Capture

## Scope

This is the practical private-alpha launch path for BJJ Tracker without automated WhatsApp capture. WhatsApp phone collection can remain in onboarding, but inbound capture must stay disabled until the privacy, auth, webhook, and database work in the go-live audit is complete.

## Current Runtime Shape

- Backend: FastAPI, SQLAlchemy, SQLite, `uvicorn`.
- Frontend: React/Vite static build.
- Health check: `GET /health` returns `{"status":"ok"}`.
- API docs: `GET /docs`.
- Local database default: `data/bjj.db`.
- Production database for private alpha: SQLite on a durable mounted volume.
- Production database recommendation before team launch: managed Postgres plus Alembic migrations and removal of SQLite-only startup compatibility patches.

## Required Backend Environment

Set these on the backend host:

```bash
BJJ_CORS_ORIGINS=https://YOUR_FRONTEND_DOMAIN
BJJ_FRONTEND_URL=https://YOUR_FRONTEND_DOMAIN
BJJ_SQLITE_PATH=/var/lib/bjj-tracker/bjj.db
BJJ_DEV_AUTH_TOKENS=false
BJJ_AUTH_REQUEST_LIMIT=5
BJJ_AUTH_REQUEST_WINDOW_MINUTES=15
```

SMTP sign-in email delivery:

```bash
BJJ_EMAIL_FROM="BJJ Tracker <no-reply@YOUR_DOMAIN>"
BJJ_SMTP_HOST=smtp.YOUR_PROVIDER.com
BJJ_SMTP_PORT=465
BJJ_SMTP_USERNAME=your-smtp-user
BJJ_SMTP_PASSWORD=your-smtp-password
BJJ_SMTP_USE_SSL=true
BJJ_SMTP_USE_TLS=false
```

`BJJ_FRONTEND_URL` is used to build sign-in links like
`https://YOUR_FRONTEND_DOMAIN/login?token=...`.

Optional shared API-key guard:

```bash
BJJ_TRACKER_API_KEY=long-random-shared-api-key
```

If this is enabled, set matching `VITE_API_KEY` for the frontend. Quick Log uses the shared frontend API client, so it sends the same session and optional API-key headers as the rest of the app.

Optional Oura variables:

```bash
OURA_CLIENT_ID=your-oura-client-id
OURA_CLIENT_SECRET=your-oura-client-secret
OURA_REDIRECT_URI=https://YOUR_BACKEND_DOMAIN/oura/callback
```

Leave WhatsApp capture unset for launch:

```bash
# Do not set for initial production:
# BJJ_ENABLE_WHATSAPP_CAPTURE=true
```

If WhatsApp capture is enabled later, also set `BJJ_META_VERIFY_TOKEN` and `BJJ_META_APP_SECRET`, then follow `docs/superpowers/specs/2026-05-18-meta-whatsapp-production-setup.md`.

## Required Frontend Environment

Set these before building the Vite app:

```bash
VITE_API_URL=https://YOUR_BACKEND_DOMAIN
# Required only when BJJ_TRACKER_API_KEY is enabled on the backend:
# VITE_API_KEY=the-same-value-as-BJJ_TRACKER_API_KEY
```

`VITE_API_KEY` is shipped to the browser. Treat it as a launch guard against casual traffic, not as real user security. User session auth still depends on `x-session-token`.

## Build And Deploy

Backend:

```bash
cd backend
python -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
```

Run the backend behind HTTPS using the deployment platform's TLS termination or a reverse proxy. Do not expose plain HTTP publicly.

Frontend:

```bash
cd frontend
npm ci
npm run build
```

Deploy `frontend/dist` to a static HTTPS host. Make sure `VITE_API_URL` points at the public HTTPS backend before the build runs.

## CORS And Auth Checks

- `BJJ_CORS_ORIGINS` must exactly include the deployed frontend origin, for example `https://bjj-tracker.example.com`.
- Do not use `*` with credentials or session flows.
- If `BJJ_TRACKER_API_KEY` is set, frontend requests must send matching `VITE_API_KEY`.
- Keep `BJJ_DEV_AUTH_TOKENS=false` in production so auth links are not returned in API responses.
- Verify SMTP delivery before inviting users. `POST /auth/request-link` should return the generic success message and the email should contain a `/login?token=...` link.
- Current magic-link/session auth is acceptable for private alpha. Before a broader trusted team pilot, add secure cookies or hardened token storage, session rotation review, and monitoring.

## SQLite Backup And Restore

SQLite is acceptable for a one-person or very small private alpha if the database file lives on a durable disk and only one backend instance writes to it.

Backup while the app is running:

```bash
mkdir -p backups
sqlite3 /var/lib/bjj-tracker/bjj.db ".backup 'backups/bjj-$(date +%Y%m%d-%H%M%S).db'"
```

Restore:

```bash
systemctl stop bjj-tracker
cp /var/lib/bjj-tracker/bjj.db /var/lib/bjj-tracker/bjj.db.pre-restore
cp backups/bjj-YYYYMMDD-HHMMSS.db /var/lib/bjj-tracker/bjj.db
systemctl start bjj-tracker
```

Rehearse restore before inviting users. Keep backups encrypted because Oura tokens and journal text may be in the database.

## Smoke Tests

Run after every deploy:

```bash
curl -fsS https://YOUR_BACKEND_DOMAIN/health
curl -fsS https://YOUR_BACKEND_DOMAIN/openapi.json >/dev/null
curl -i -H "Origin: https://YOUR_FRONTEND_DOMAIN" https://YOUR_BACKEND_DOMAIN/health
```

Browser checks:

- Open the frontend over HTTPS.
- Request a magic link for a test email.
- Confirm production responses do not include `dev_token`.
- Confirm the sign-in email arrives and opens `/login?token=...`.
- Sign in through the emailed link.
- Create a private note, session, and technique.
- Refresh the dashboard and confirm only the signed-in user's records appear.
- Confirm WhatsApp webhook verification returns 404 while `BJJ_ENABLE_WHATSAPP_CAPTURE` is unset.

## Rollback

Frontend rollback:

- Redeploy the previous static build artifact.
- Keep `VITE_API_URL` pointed at the same backend unless the backend also rolled back.

Backend rollback:

- Stop the current backend process.
- Restore the previous backend release.
- Keep the same `BJJ_SQLITE_PATH`.
- If schema changes were applied, restore the matching SQLite backup.
- Run the smoke tests before reopening access.

## Remaining Blockers For Team Launch

- Full user ownership isolation for every journal object and dashboard path must remain covered by tests.
- Auth now supports SMTP sign-in email delivery. It still needs a stronger browser session strategy before broader trusted team use.
- SQLite has no migration discipline today; add Alembic before real multi-user data.
- Postgres is recommended for team launch, but should be introduced with migrations and a tested backup/restore path.
- Keep Quick Log covered in smoke tests because `/parse` is authenticated and writes private journal records.
- Add structured logs and error monitoring without logging journal text, tokens, or Oura secrets.
