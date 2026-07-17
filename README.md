# BJJ Tracker

Personal Brazilian Jiu-Jitsu training journal. Built for Purple Belt, 2 Stripes.

## Production

- App: https://bjj-notebook.com (Cloudflare Workers static assets, project `bjj-notebook`, deploys from `main`)
- API: https://bjj-tracker-api-lc3n.onrender.com (Render web service `bjj-tracker-api`, deploys from `main`, SQLite on a persistent disk)
- Sign-in emails: Resend via `send.bjj-notebook.com`

## Stack
- **Backend:** FastAPI + SQLite + SQLAlchemy
- **Frontend:** React + Vite + Tailwind CSS + Recharts

## Quick Start

```bash
cd ~/projects/bjj-tracker
./start.sh
```

Then open: **http://localhost:5173**

API docs: http://localhost:8000/docs

## Manual Start

**Backend:**
```bash
cd backend
source venv/bin/activate
python -m uvicorn main:app --host 127.0.0.1 --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm run dev
```

## Features
- Session log with attendance tracking
- Technique library (CRUD, search, tags, proficiency levels)
- Roll log with submission/position tracking
- Progress tracker with rank history + weekly chart
- Free-form notes scratchpad
- Dashboard with streak, spotlight technique, recent sessions
- Optional WhatsApp phone on athlete profiles for future capture/contact workflows

## WhatsApp Capture

WhatsApp capture is intentionally disabled for initial go-live so deployment is not blocked on Meta configuration.

The first-party Meta webhook code exists behind an explicit feature flag:

```bash
BJJ_ENABLE_WHATSAPP_CAPTURE=true
BJJ_META_VERIFY_TOKEN=your-verify-token
BJJ_META_APP_SECRET=your-meta-app-secret
```

Leave `BJJ_ENABLE_WHATSAPP_CAPTURE` unset for the first production launch.

## Auth

Magic links and session tokens are stored in `auth_tokens` with an expiry. By default, sign-in links expire after 15 minutes and sessions after 720 hours.

`/auth/request-link` returns a safe generic message in normal environments. It sends a sign-in email when SMTP is configured. It only includes a `dev_token` when `BJJ_DEV_AUTH_TOKENS=true`, which is for local development or a tightly controlled private pilot only.

Auth-related environment knobs:

```bash
BJJ_DEV_AUTH_TOKENS=false
BJJ_FRONTEND_URL=https://bjj-tracker.example.com
BJJ_EMAIL_FROM="BJJ Tracker <no-reply@example.com>"
BJJ_SMTP_HOST=smtp.example.com
BJJ_SMTP_PORT=465
BJJ_SMTP_USERNAME=replace-with-smtp-user
BJJ_SMTP_PASSWORD=replace-with-smtp-password
BJJ_SMTP_USE_SSL=true
BJJ_SMTP_USE_TLS=false
BJJ_AUTH_MAGIC_LINK_TTL_MINUTES=15
BJJ_AUTH_SESSION_TTL_HOURS=720
BJJ_AUTH_REQUEST_LIMIT=5
BJJ_AUTH_REQUEST_WINDOW_MINUTES=15
```

## Data
SQLite database: `data/bjj.db` — single file, easy to back up.

For launch deployment without WhatsApp capture, use the runbook:
`docs/superpowers/specs/2026-05-30-launch-runbook-without-whatsapp.md`.

Sample environment files:
- `backend/.env.example`
- `frontend/.env.example`

## Local Security
- Backend and frontend default to `127.0.0.1` so the app stays local.
- CORS defaults to local Vite origins only. Override with `BJJ_CORS_ORIGINS` if needed.
- Optional API key protection is available by setting `BJJ_TRACKER_API_KEY` for the backend and `VITE_API_KEY` for the frontend.
- Oura tokens live in SQLite today; treat `data/bjj.db` as sensitive.

## Checks
```bash
python -m unittest tests/test_contracts.py
cd frontend
npm run lint
npm run build
```
