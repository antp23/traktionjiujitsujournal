"""Oura Ring integration: OAuth handshake, daily sync, stored recovery data.

v1 quirk kept deliberately: Oura data is a process-global singleton (one
athlete per deployment) and these endpoints manage their own sessions on the
global engine rather than the request-scoped dependency.
"""
import json
from datetime import date, datetime, timedelta
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse

from app import config
from app.db import SessionLocal
from app.models import OuraDaily, OuraToken

router = APIRouter(prefix="/oura", tags=["oura"])

OURA_AUTH_URL = "https://cloud.ouraring.com/oauth/authorize"
OURA_TOKEN_URL = "https://api.ouraring.com/oauth/token"
OURA_API_BASE = "https://api.ouraring.com/v2"


def _stored_token() -> Optional[OuraToken]:
    with SessionLocal() as session:
        return session.query(OuraToken).first()


def _oura_error(message: str, status_code: int = 502) -> None:
    raise HTTPException(status_code=status_code, detail=message)


async def _refresh_access_token(refresh_token: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(OURA_TOKEN_URL, data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": config.oura_client_id(),
                "client_secret": config.oura_client_secret(),
            })
    except httpx.TimeoutException:
        _oura_error("Oura token refresh timed out. Try syncing again in a minute.", 504)
    except httpx.HTTPError:
        _oura_error("Could not reach Oura while refreshing the token.")

    if response.status_code != 200:
        _oura_error("Failed to refresh Oura token. Reconnect Oura from the Recovery page.", 401)

    data = response.json()
    with SessionLocal() as session:
        token_row = session.query(OuraToken).first()
        if token_row:
            token_row.access_token = data["access_token"]
            token_row.refresh_token = data.get("refresh_token", token_row.refresh_token)
            token_row.updated_at = datetime.utcnow()
        session.commit()
    return data["access_token"]


async def _valid_access_token() -> str:
    token_row = _stored_token()
    if not token_row:
        raise HTTPException(
            status_code=401,
            detail="Oura not connected. Visit /oura/auth to authorize.",
        )
    return await _refresh_access_token(token_row.refresh_token)


@router.get("/auth")
def oura_auth():
    """Redirect the user to Oura's OAuth consent page."""
    scopes = "daily sleep heartrate workout tag"
    url = (
        f"{OURA_AUTH_URL}"
        f"?response_type=code"
        f"&client_id={config.oura_client_id()}"
        f"&redirect_uri={config.oura_redirect_uri()}"
        f"&scope={scopes}"
    )
    return RedirectResponse(url)


@router.get("/callback")
async def oura_callback(code: str = None, error: str = None):
    """Exchange the OAuth code and store the token pair."""
    if error or not code:
        raise HTTPException(status_code=400, detail=f"Oura auth error: {error}")

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(OURA_TOKEN_URL, data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": config.oura_redirect_uri(),
                "client_id": config.oura_client_id(),
                "client_secret": config.oura_client_secret(),
            })
    except httpx.TimeoutException:
        _oura_error("Oura authorization timed out. Try connecting again.", 504)
    except httpx.HTTPError:
        _oura_error("Could not reach Oura during authorization.")

    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Token exchange failed. Try connecting Oura again.")
    data = response.json()

    with SessionLocal() as session:
        existing = session.query(OuraToken).first()
        if existing:
            existing.access_token = data["access_token"]
            existing.refresh_token = data["refresh_token"]
            existing.updated_at = datetime.utcnow()
        else:
            session.add(OuraToken(
                access_token=data["access_token"],
                refresh_token=data["refresh_token"],
            ))
        session.commit()

    return HTMLResponse("""
        <html><body style="font-family:sans-serif;text-align:center;padding:60px;background:#111;color:#fff">
        <h2>✅ Oura Connected!</h2>
        <p>You can close this tab and return to your BJJ Tracker.</p>
        <p><a href="http://localhost:5173" style="color:#00ff88">Go to Dashboard →</a></p>
        </body></html>
    """)


@router.get("/status")
def oura_status():
    token_row = _stored_token()
    if token_row:
        return {"connected": True, "updated_at": token_row.updated_at}
    return {"connected": False}


@router.post("/sync")
async def oura_sync(days: int = 30):
    """Pull readiness, sleep, and HRV data for the last N days and upsert it."""
    access_token = await _valid_access_token()
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    headers = {"Authorization": f"Bearer {access_token}"}
    window = {"start_date": str(start_date), "end_date": str(end_date)}

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            readiness_resp = await client.get(
                f"{OURA_API_BASE}/usercollection/daily_readiness",
                headers=headers, params=window,
            )
            sleep_resp = await client.get(
                f"{OURA_API_BASE}/usercollection/daily_sleep",
                headers=headers, params=window,
            )
            hrv_resp = await client.get(
                f"{OURA_API_BASE}/usercollection/sleep",
                headers=headers, params=window,
            )
    except httpx.TimeoutException:
        _oura_error("Oura sync timed out. Your existing recovery data is still intact.", 504)
    except httpx.HTTPError:
        _oura_error("Could not reach Oura. Your existing recovery data is still intact.")

    for response in (readiness_resp, sleep_resp, hrv_resp):
        if response.status_code == 401:
            _oura_error("Oura authorization expired. Reconnect Oura from the Recovery page.", 401)
        if response.status_code >= 400:
            _oura_error("Oura returned an error while syncing. Try again later.")

    readiness_data = {r["day"]: r for r in readiness_resp.json().get("data", [])}
    sleep_data = {s["day"]: s for s in sleep_resp.json().get("data", [])}

    # HRV, resting HR, and actual sleep duration come from long-sleep periods.
    hrv_by_day: dict[str, int] = {}
    rhr_by_day: dict[str, int] = {}
    sleep_minutes_by_day: dict[str, int] = {}
    for period in hrv_resp.json().get("data", []):
        day = period.get("day")
        if not day or period.get("type") != "long_sleep":
            continue
        if period.get("average_hrv"):
            hrv_by_day[day] = period["average_hrv"]
        if period.get("lowest_heart_rate"):
            rhr_by_day[day] = period["lowest_heart_rate"]
        if period.get("total_sleep_duration"):
            sleep_minutes_by_day[day] = round(period["total_sleep_duration"] / 60)

    synced = 0
    with SessionLocal() as session:
        for day_str in set(readiness_data) | set(sleep_data):
            readiness = readiness_data.get(day_str, {})
            sleep = sleep_data.get(day_str, {})
            temperature = readiness.get("contributors", {}).get("body_temperature")
            row_data = {
                "readiness_score": readiness.get("score"),
                "sleep_score": sleep.get("score"),
                "hrv_avg": hrv_by_day.get(day_str),
                "resting_hr": rhr_by_day.get(day_str),
                "total_sleep_minutes": sleep_minutes_by_day.get(day_str),
                "temperature_deviation": str(temperature) if temperature else None,
                "raw": json.dumps({"readiness": readiness, "sleep": sleep}),
            }

            existing = session.query(OuraDaily).filter(OuraDaily.date == day_str).first()
            if existing:
                for field, value in row_data.items():
                    setattr(existing, field, value)
            else:
                session.add(OuraDaily(date=day_str, **row_data))
            synced += 1
        session.commit()

    return {"synced": synced, "start_date": str(start_date), "end_date": str(end_date)}


@router.get("/data")
def oura_data(days: int = 30):
    """Return stored recovery data for the last N days, newest first."""
    start_date = date.today() - timedelta(days=days)
    with SessionLocal() as session:
        rows = (
            session.query(OuraDaily)
            .filter(OuraDaily.date >= str(start_date))
            .order_by(OuraDaily.date.desc())
            .all()
        )
        return [
            {
                "date": str(row.date),
                "readiness_score": row.readiness_score,
                "sleep_score": row.sleep_score,
                "hrv_avg": row.hrv_avg,
                "resting_hr": row.resting_hr,
                "total_sleep_minutes": row.total_sleep_minutes,
                "temperature_deviation": row.temperature_deviation,
            }
            for row in rows
        ]
