# Meta WhatsApp Production Setup

## Status

Deferred for initial go-live.

The backend webhook code exists, but it is disabled unless this env var is set:

```bash
BJJ_ENABLE_WHATSAPP_CAPTURE=true
```

Leave that env var unset for the first production launch.

## Backend Endpoint

Configure Meta WhatsApp Cloud API webhooks to use:

```text
https://YOUR_BACKEND_DOMAIN/webhooks/whatsapp/meta
```

Local development URL:

```text
http://127.0.0.1:8000/webhooks/whatsapp/meta
```

Meta requires a public HTTPS URL for production webhook verification.

## Required Backend Environment Variables

```bash
BJJ_META_VERIFY_TOKEN=choose-a-long-random-string
BJJ_META_APP_SECRET=meta-app-secret
```

Optional for the next outbound-confirmation step:

```bash
BJJ_META_ACCESS_TOKEN=system-user-or-permanent-access-token
BJJ_META_PHONE_NUMBER_ID=meta-phone-number-id
```

## Meta Dashboard Steps

1. Create or open the Meta app connected to the WhatsApp Business Account.
2. Add the WhatsApp product if it is not already present.
3. Add or select the production WhatsApp business phone number.
4. Configure the webhook callback URL:
   `https://YOUR_BACKEND_DOMAIN/webhooks/whatsapp/meta`
5. Set the verify token to the exact value of `BJJ_META_VERIFY_TOKEN`.
6. Subscribe the app to WhatsApp `messages` webhook events.
7. Send a WhatsApp message from the enrolled athlete phone to the business number.

## App Behavior

When a text message arrives:

1. The backend verifies `X-Hub-Signature-256` with `BJJ_META_APP_SECRET`.
2. The backend dedupes by Meta message ID.
3. The backend normalizes the sender phone number.
4. The backend matches it to `WhatsAppIdentity.phone`.
5. The backend stores an `InboundMessage`.
6. If the phone is known, the backend parses the text into a private journal object.
7. If the phone is unknown, the backend stores the inbound message as unmatched and does not create journal records.

## Enrollment Requirement

The athlete must have a matching WhatsApp phone in onboarding, for example:

```text
+15555555555
```

The backend normalizes Meta's inbound `15555555555` sender format to `+15555555555`.

## Local Verification

Start the backend with:

```bash
cd backend
BJJ_META_VERIFY_TOKEN=verify-me BJJ_META_APP_SECRET=app-secret ./venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Check the webhook challenge route:

```bash
curl -i 'http://127.0.0.1:8000/webhooks/whatsapp/meta?hub.mode=subscribe&hub.verify_token=verify-me&hub.challenge=challenge-123'
```

Expected:

```text
HTTP/1.1 200 OK
challenge-123
```

## OpenClaw Note

OpenClaw can still be used downstream for interpretation or advice, but Meta should call this backend first. This keeps signature verification, dedupe, phone-to-athlete routing, and privacy ownership inside the product.
