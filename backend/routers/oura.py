import os
import httpx
import json
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from datetime import date, timedelta, datetime
from database import SessionLocal
from models import OuraToken, OuraDaily
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

router = APIRouter(prefix="/oura", tags=["oura"])

OURA_CLIENT_ID = os.getenv("OURA_CLIENT_ID")
OURA_CLIENT_SECRET = os.getenv("OURA_CLIENT_SECRET")
OURA_REDIRECT_URI = os.getenv("OURA_REDIRECT_URI", "http://localhost:8000/oura/callback")
OURA_AUTH_URL = "https://cloud.ouraring.com/oauth/authorize"
OURA_TOKEN_URL = "https://api.ouraring.com/oauth/token"
OURA_API_BASE = "https://api.ouraring.com/v2"


def get_token_from_db():
    db = SessionLocal()
    try:
        token_row = db.query(OuraToken).first()
        return token_row
    finally:
        db.close()


def raise_oura_error(message: str, status_code: int = 502):
    raise HTTPException(status_code=status_code, detail=message)


async def refresh_access_token(refresh_token: str):
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(OURA_TOKEN_URL, data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": OURA_CLIENT_ID,
                "client_secret": OURA_CLIENT_SECRET,
            })
    except httpx.TimeoutException:
        raise_oura_error("Oura token refresh timed out. Try syncing again in a minute.", 504)
    except httpx.HTTPError:
        raise_oura_error("Could not reach Oura while refreshing the token.")

    if resp.status_code != 200:
        raise_oura_error("Failed to refresh Oura token. Reconnect Oura from the Recovery page.", 401)

    data = resp.json()
    db = SessionLocal()
    try:
        token_row = db.query(OuraToken).first()
        if token_row:
            token_row.access_token = data["access_token"]
            token_row.refresh_token = data.get("refresh_token", token_row.refresh_token)
            token_row.updated_at = datetime.utcnow()
        db.commit()
        return data["access_token"]
    finally:
        db.close()


async def get_valid_access_token():
    token_row = get_token_from_db()
    if not token_row:
        raise HTTPException(status_code=401, detail="Oura not connected. Visit /oura/auth to authorize.")
    return await refresh_access_token(token_row.refresh_token)


@router.get("/auth")
def oura_auth():
    """Redirect user to Oura OAuth authorization page."""
    scopes = "daily sleep heartrate workout tag"
    url = (
        f"{OURA_AUTH_URL}"
        f"?response_type=code"
        f"&client_id={OURA_CLIENT_ID}"
        f"&redirect_uri={OURA_REDIRECT_URI}"
        f"&scope={scopes}"
    )
    return RedirectResponse(url)


@router.get("/callback")
async def oura_callback(code: str = None, error: str = None):
    """Handle OAuth callback from Oura."""
    if error or not code:
        raise HTTPException(status_code=400, detail=f"Oura auth error: {error}")

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(OURA_TOKEN_URL, data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": OURA_REDIRECT_URI,
                "client_id": OURA_CLIENT_ID,
                "client_secret": OURA_CLIENT_SECRET,
            })
    except httpx.TimeoutException:
        raise_oura_error("Oura authorization timed out. Try connecting again.", 504)
    except httpx.HTTPError:
        raise_oura_error("Could not reach Oura during authorization.")

    if resp.status_code != 200:
        raise HTTPException(status_code=400, detail="Token exchange failed. Try connecting Oura again.")
    data = resp.json()

    db = SessionLocal()
    try:
        existing = db.query(OuraToken).first()
        if existing:
            existing.access_token = data["access_token"]
            existing.refresh_token = data["refresh_token"]
            existing.updated_at = datetime.utcnow()
        else:
            db.add(OuraToken(
                access_token=data["access_token"],
                refresh_token=data["refresh_token"],
            ))
        db.commit()
    finally:
        db.close()

    return HTMLResponse("""
        <html><body style="font-family:sans-serif;text-align:center;padding:60px;background:#111;color:#fff">
        <h2>✅ Oura Connected!</h2>
        <p>You can close this tab and return to your BJJ Tracker.</p>
        <p><a href="http://localhost:5173" style="color:#00ff88">Go to Dashboard →</a></p>
        </body></html>
    """)


@router.get("/status")
def oura_status():
    """Check if Oura is connected."""
    token_row = get_token_from_db()
    if token_row:
        return {"connected": True, "updated_at": token_row.updated_at}
    return {"connected": False}


@router.post("/sync")
async def oura_sync(days: int = 30):
    """Pull Oura data for the last N days and store it."""
    access_token = await get_valid_access_token()
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            readiness_resp = await client.get(
                f"{OURA_API_BASE}/usercollection/daily_readiness",
                headers=headers,
                params={"start_date": str(start_date), "end_date": str(end_date)}
            )
            sleep_resp = await client.get(
                f"{OURA_API_BASE}/usercollection/daily_sleep",
                headers=headers,
                params={"start_date": str(start_date), "end_date": str(end_date)}
            )
            hrv_resp = await client.get(
                f"{OURA_API_BASE}/usercollection/sleep",
                headers=headers,
                params={"start_date": str(start_date), "end_date": str(end_date)}
            )
    except httpx.TimeoutException:
        raise_oura_error("Oura sync timed out. Your existing recovery data is still intact.", 504)
    except httpx.HTTPError:
        raise_oura_error("Could not reach Oura. Your existing recovery data is still intact.")

    for resp in (readiness_resp, sleep_resp, hrv_resp):
        if resp.status_code == 401:
            raise_oura_error("Oura authorization expired. Reconnect Oura from the Recovery page.", 401)
        if resp.status_code >= 400:
            raise_oura_error("Oura returned an error while syncing. Try again later.")

    readiness_data = {r["day"]: r for r in readiness_resp.json().get("data", [])}
    sleep_data = {s["day"]: s for s in sleep_resp.json().get("data", [])}

    # HRV + resting HR + actual sleep duration from sleep periods (seconds → minutes)
    hrv_by_day = {}
    rhr_by_day = {}
    sleep_minutes_by_day = {}
    for s in hrv_resp.json().get("data", []):
        day = s.get("day")
        if day and s.get("type") == "long_sleep":
            if s.get("average_hrv"):
                hrv_by_day[day] = s["average_hrv"]
            if s.get("lowest_heart_rate"):
                rhr_by_day[day] = s["lowest_heart_rate"]
            if s.get("total_sleep_duration"):
                sleep_minutes_by_day[day] = round(s["total_sleep_duration"] / 60)

    db = SessionLocal()
    synced = 0
    try:
        all_days = set(list(readiness_data.keys()) + list(sleep_data.keys()))
        for day_str in all_days:
            r = readiness_data.get(day_str, {})
            s = sleep_data.get(day_str, {})

            existing = db.query(OuraDaily).filter(OuraDaily.date == day_str).first()
            row_data = {
                "readiness_score": r.get("score"),
                "sleep_score": s.get("score"),
                "hrv_avg": hrv_by_day.get(day_str),
                "resting_hr": rhr_by_day.get(day_str),
                "total_sleep_minutes": sleep_minutes_by_day.get(day_str),
                "temperature_deviation": str(r.get("contributors", {}).get("body_temperature")) if r.get("contributors", {}).get("body_temperature") else None,
                "raw": json.dumps({"readiness": r, "sleep": s}),
            }

            if existing:
                for k, v in row_data.items():
                    setattr(existing, k, v)
            else:
                db.add(OuraDaily(date=day_str, **row_data))
            synced += 1

        db.commit()
    finally:
        db.close()

    return {"synced": synced, "start_date": str(start_date), "end_date": str(end_date)}


@router.get("/data")
def oura_data(days: int = 30):
    """Return stored Oura data for the last N days."""
    start_date = date.today() - timedelta(days=days)
    db = SessionLocal()
    try:
        rows = (
            db.query(OuraDaily)
            .filter(OuraDaily.date >= str(start_date))
            .order_by(OuraDaily.date.desc())
            .all()
        )
        return [
            {
                "date": str(r.date),
                "readiness_score": r.readiness_score,
                "sleep_score": r.sleep_score,
                "hrv_avg": r.hrv_avg,
                "resting_hr": r.resting_hr,
                "total_sleep_minutes": r.total_sleep_minutes,
                "temperature_deviation": r.temperature_deviation,
            }
            for r in rows
        ]
    finally:
        db.close()
