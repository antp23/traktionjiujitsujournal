# Go-Live Readiness Audit

## Verdict

The app is in a strong personal-prototype state and is now much closer to a believable team product, but it is not ready for gym-wide go-live yet.

It is ready for:

- Personal daily testing.
- Demoing the team workspace concept.
- A tightly controlled pilot with your own account after privacy fixes.

It is not ready for:

- Inviting the whole gym.
- Storing real athlete journals in production.
- Letting coaches use it with trust that private notes cannot leak.
- Automated WhatsApp capture. This is now explicitly deferred for initial go-live.

The main issue is not the UI anymore. The current blocker is data ownership and production trust.

## P0 Before Any Real Team Launch

### 1. Scope Every Personal Object By User

Current state:

- Goals are user-scoped.
- Team workspace, membership, athlete profile, and WhatsApp identity exist.
- Notes are not safely scoped.
- Sessions, techniques, rolls, rank logs, dashboard data, and quick parse output are still mostly global/personal.

Risk:

If multiple athletes use the same deployed instance, one athlete's training data can appear in another user's journal/dashboard unless every personal endpoint filters by authenticated user.

Required:

- Add `owner_user_id` to notes, sessions, techniques, rolls, rank logs, and any future journal object.
- Require session auth on journal-writing endpoints.
- Filter list/detail/update/delete routes by `owner_user_id`.
- Make dashboard and analytics use only the current user's data.
- Keep coach visibility opt-in through shared threads only.

### 2. Fix Note And Sharing Ownership

Current state:

- `GET /notes` returns all notes.
- `POST /notes` creates notes without authenticated ownership.
- Sharing can attach ownership to an unowned note at share time.

Risk:

This is the highest privacy-risk area because notes are exactly where candid coach feedback and personal reflections will live.

Required:

- Require `x-session-token` for notes.
- Set `Note.owner_user_id` on create.
- Reject sharing any note not owned by the current user.
- Remove the migration-style behavior that assigns ownership during sharing.

### 3. Authenticate Quick Capture And Parser Writes

Current state:

- Quick parse endpoints can create sessions, notes, and techniques without user context.
- Parser output still writes into global tables.

Risk:

WhatsApp capture will amplify this problem if inbound messages do not resolve to a single athlete before writing data.

Required:

- Pass authenticated `current_user` into parse actions.
- Make parser-created records private by default.
- For WhatsApp, map inbound phone numbers to `WhatsAppIdentity.user_id` before parsing.
- Store the raw inbound capture before extracting structured records.

### 4. Harden Auth

Current state:

- Magic links are dev-friendly and return `dev_token` directly.
- Tokens do not appear to have real expiry, throttling, email delivery, rotation, or secure cookie behavior.

Required:

- Send magic links by email in production.
- Add token expiration and one-time use enforcement.
- Add rate limiting for email/token endpoints.
- Store session tokens securely and support logout/session revocation.
- Consider httpOnly cookies before production.

### 5. Replace Schema Auto-Create With Migrations

Current state:

- SQLite database with `Base.metadata.create_all`.
- Manual `ALTER TABLE` compatibility patches in app startup.

Required:

- Add Alembic migrations.
- Move production to managed Postgres or another durable hosted database.
- Keep SQLite only for local development.
- Add backup/export strategy before real athlete data exists.

### 6. Production Deployment Basics

Required:

- Hosted HTTPS frontend and backend.
- Environment-driven API URL, CORS origins, secrets, DB URL, email provider keys, and WhatsApp provider keys.
- Structured logs without leaking journal text or tokens.
- Error monitoring.
- Health check endpoint.
- Basic backup/restore rehearsal.

## P1 Before A Trusted Team Pilot

### Deferred WhatsApp Capture

- Leave `BJJ_ENABLE_WHATSAPP_CAPTURE` unset for initial production.
- Keep WhatsApp phone as optional profile/contact detail.
- Do not configure Meta webhooks until the core product is stable in production.
- Re-enable capture later by setting `BJJ_ENABLE_WHATSAPP_CAPTURE=true` and completing the Meta setup doc.

### Team Administration

- Invite rotation and deactivation.
- Member list with role/status.
- Remove/deactivate member.
- Prevent accidental duplicate workspace bootstraps.
- Make owner/admin flows impossible to confuse with athlete flows.

### Privacy UX

- Every shared goal/note should show a clear shared/private state.
- Sharing action should be explicit and reversible where possible.
- Coach inbox should only include explicitly shared items.
- Coach replies should be clearly separate from private journal notes.

### Fresh User Experience

- Empty dashboard for a new athlete should feel useful, not broken.
- First journal capture should guide the athlete toward high-detail inputs.
- Onboarding should collect WhatsApp phone, belt, training frequency, current focus, problem positions, limitations, and consent.

### Data Control

- Athlete export of their own journal.
- Delete account or at least deactivate/export path.
- Admin can remove an athlete from workspace without deleting the athlete's private history.

## P2 After Pilot

- Coach Brief intelligence that synthesizes goals, logs, repeated problems, and coach replies.
- Dedicated Coach Notes lifecycle: active, internalized, archived.
- Mobile polish for mat-side and car-after-training capture.
- Oura integration hardening and explicit privacy treatment.
- Bundle splitting for frontend build size.
- More complete test coverage around auth, privacy, and route access.

## WhatsApp Readiness

### Current State

The app collects WhatsApp phone details during onboarding and stores them as an athlete identity. That is necessary, but it is not a WhatsApp integration yet.

There is currently no:

- WhatsApp inbound webhook.
- Provider signature verification.
- Provider message ID dedupe.
- Phone-number-to-athlete routing in the parser.
- Consent record for automated WhatsApp capture.
- Outbound confirmation or error flow.

### Important Product Decision

Do not wire this by logging into or scraping your personal WhatsApp account.

Use an official WhatsApp Business route:

- Twilio WhatsApp Sandbox for fastest personal/dev pilot.
- Twilio production WhatsApp sender for a managed provider path.
- Meta WhatsApp Business Cloud API for direct production integration.

Official references checked:

- Meta WhatsApp Cloud API: https://developers.facebook.com/docs/whatsapp/cloud-api/
- Meta webhooks and Cloud API docs: https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks/
- Twilio WhatsApp quickstart/sandbox: https://www.twilio.com/docs/whatsapp/quickstart

### Recommended Path

For the next build:

1. Keep WhatsApp phone collection in enrollment.
2. Add a provider-neutral `InboundMessage` table and webhook route.
3. Implement Twilio Sandbox first because it is fastest to test with your own phone.
4. Route inbound messages by phone number to `WhatsAppIdentity.user_id`.
5. Save every inbound message as a private raw journal capture.
6. Feed the raw text into the same parser used by Quick Log, but with `owner_user_id`.
7. Return a short confirmation message.

For gym-wide use:

- Move to a production WhatsApp sender through Twilio or direct Meta Cloud API.
- Use a business number, not your personal WhatsApp account.
- Add explicit opt-in language during enrollment.
- Treat all inbound WhatsApp captures as private by default.

### Minimal WhatsApp Architecture

Add:

- `POST /webhooks/whatsapp/twilio`
- `POST /webhooks/whatsapp/meta` later if direct Meta is chosen
- `InboundMessage` model:
  - `id`
  - `provider`
  - `provider_message_id`
  - `from_phone`
  - `to_phone`
  - `owner_user_id`
  - `raw_body`
  - `parsed_status`
  - `received_at`

Processing flow:

1. Provider sends inbound webhook.
2. Backend verifies provider signature.
3. Backend dedupes by provider message ID.
4. Backend normalizes sender phone number.
5. Backend finds `WhatsAppIdentity`.
6. Backend stores raw private capture.
7. Backend parses into notes/sessions/techniques with `owner_user_id`.
8. Backend responds with acknowledgement.

Privacy rule:

WhatsApp capture is athlete-only unless the athlete explicitly shares a resulting note, goal, or thread.

## Recommended Implementation Sequence

1. Privacy hardening: user-scope notes, sessions, techniques, rolls, rank logs, dashboard, and parser writes.
2. Auth hardening: expiring links, email delivery, sessions, logout, rate limits.
3. Database hardening: Alembic and hosted production DB.
4. Team pilot: invite 1-2 trusted athletes and one coach.
5. Go-live: only after privacy tests prove cross-user isolation.
6. WhatsApp capture: enable later after the core production launch is stable.

## Go-Live Bar

The app should only go live for the gym when these tests pass:

- Athlete A cannot see Athlete B's notes, sessions, goals, rolls, or dashboard data.
- Coach cannot see private athlete records.
- Coach can see only explicitly shared notes/goals/threads.
- WhatsApp message from Athlete A creates only Athlete A records.
- Unknown WhatsApp phone number does not create records.
- Expired magic links cannot log in.
- Invite links can be revoked.
- Production secrets are not committed or exposed to the browser.

Until then, the right move is a private alpha, not a team launch.
