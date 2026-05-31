from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import date
from database import engine, Base, get_db
from sqlalchemy.orm import Session as DBSession
import models
from routers import sessions, techniques, rolls, rank, notes, coaches, parse, oura, auth, workspaces, goals, sharing, whatsapp
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

app = FastAPI(title="BJJ Tracker API", version="1.0.0")

def _csv_env(name: str, default: str):
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_csv_env("BJJ_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sessions.router)
app.include_router(techniques.router)
app.include_router(rolls.router)
app.include_router(rank.router)
app.include_router(notes.router)
app.include_router(coaches.router)
app.include_router(parse.router)
app.include_router(oura.router)
app.include_router(auth.router)
app.include_router(workspaces.router)
app.include_router(goals.router)
app.include_router(sharing.router)
app.include_router(whatsapp.router)

PUBLIC_PATHS = {"/health", "/docs", "/openapi.json", "/redoc", "/oura/callback"}
SESSION_AUTH_PREFIXES = (
    "/auth",
    "/workspaces",
    "/goals",
    "/sharing",
    "/notes",
    "/sessions",
    "/techniques",
    "/rolls",
    "/rank",
    "/parse",
    "/dashboard",
)


@app.middleware("http")
async def require_api_key(request: Request, call_next):
    api_key = os.getenv("BJJ_TRACKER_API_KEY")
    if (
        not api_key
        or request.url.path in PUBLIC_PATHS
        or request.url.path.startswith("/docs/")
        or request.url.path.startswith(SESSION_AUTH_PREFIXES)
    ):
        return await call_next(request)
    if request.headers.get("x-api-key") != api_key:
        return JSONResponse({"detail": "Invalid or missing API key"}, status_code=401)
    return await call_next(request)


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    _ensure_nullable_columns()


@app.get("/health")
def health():
    return {"status": "ok"}


def _ensure_nullable_columns():
    with engine.connect() as connection:
        note_columns = {
            row[1]
            for row in connection.exec_driver_sql("PRAGMA table_info(notes)").fetchall()
        }
        if "owner_user_id" not in note_columns:
            connection.exec_driver_sql("ALTER TABLE notes ADD COLUMN owner_user_id VARCHAR")
            connection.commit()

        session_columns = {
            row[1]
            for row in connection.exec_driver_sql("PRAGMA table_info(sessions)").fetchall()
        }
        if session_columns and "owner_user_id" not in session_columns:
            connection.exec_driver_sql("ALTER TABLE sessions ADD COLUMN owner_user_id VARCHAR")
            connection.commit()

        technique_columns = {
            row[1]
            for row in connection.exec_driver_sql("PRAGMA table_info(techniques)").fetchall()
        }
        if technique_columns and "owner_user_id" not in technique_columns:
            connection.exec_driver_sql("ALTER TABLE techniques ADD COLUMN owner_user_id VARCHAR")
            connection.commit()

        roll_columns = {
            row[1]
            for row in connection.exec_driver_sql("PRAGMA table_info(roll_logs)").fetchall()
        }
        if roll_columns and "owner_user_id" not in roll_columns:
            connection.exec_driver_sql("ALTER TABLE roll_logs ADD COLUMN owner_user_id VARCHAR")
            connection.commit()

        rank_columns = {
            row[1]
            for row in connection.exec_driver_sql("PRAGMA table_info(rank_logs)").fetchall()
        }
        if rank_columns and "owner_user_id" not in rank_columns:
            connection.exec_driver_sql("ALTER TABLE rank_logs ADD COLUMN owner_user_id VARCHAR")
            connection.commit()

        share_thread_columns = {
            row[1]
            for row in connection.exec_driver_sql("PRAGMA table_info(share_threads)").fetchall()
        }
        if share_thread_columns:
            if "status" not in share_thread_columns:
                connection.exec_driver_sql("ALTER TABLE share_threads ADD COLUMN status VARCHAR DEFAULT 'open' NOT NULL")
            if "updated_at" not in share_thread_columns:
                connection.exec_driver_sql("ALTER TABLE share_threads ADD COLUMN updated_at DATETIME")
                connection.exec_driver_sql("UPDATE share_threads SET updated_at = created_at WHERE updated_at IS NULL")
            connection.commit()

        thread_message_columns = {
            row[1]
            for row in connection.exec_driver_sql("PRAGMA table_info(thread_messages)").fetchall()
        }
        if thread_message_columns and "pinned_as_coach_note_id" not in thread_message_columns:
            connection.exec_driver_sql("ALTER TABLE thread_messages ADD COLUMN pinned_as_coach_note_id VARCHAR")
            connection.commit()

        auth_token_columns = {
            row[1]
            for row in connection.exec_driver_sql("PRAGMA table_info(auth_tokens)").fetchall()
        }
        if auth_token_columns:
            if "expires_at" not in auth_token_columns:
                connection.exec_driver_sql("ALTER TABLE auth_tokens ADD COLUMN expires_at DATETIME")
            connection.exec_driver_sql(
                """
                UPDATE auth_tokens
                SET expires_at = CASE
                    WHEN token_type = 'session' THEN datetime(COALESCE(created_at, CURRENT_TIMESTAMP), '+30 days')
                    ELSE datetime(COALESCE(created_at, CURRENT_TIMESTAMP), '+15 minutes')
                END
                WHERE expires_at IS NULL
                """
            )
            connection.commit()


@app.get("/dashboard")
def dashboard(
    current_user: models.User = Depends(auth.get_current_user),
    db: DBSession = Depends(get_db),
):
    from routers.sessions import _session_stats_for_owner
    from routers.rolls import _roll_stats_for_owner
    import random

    # Session stats
    stats = _session_stats_for_owner(db, current_user.user_id)

    # Current rank
    current_rank = db.query(models.RankLog).filter(
        models.RankLog.owner_user_id == current_user.user_id
    ).order_by(models.RankLog.date_awarded.desc()).first()

    # Technique counts by proficiency
    all_techniques = db.query(models.Technique).filter(
        models.Technique.owner_user_id == current_user.user_id
    ).all()
    proficiency_counts = {}
    for t in all_techniques:
        proficiency_counts[t.proficiency] = proficiency_counts.get(t.proficiency, 0) + 1

    # Recent sessions
    recent_sessions = db.query(models.Session).filter(
        models.Session.owner_user_id == current_user.user_id
    ).order_by(
        models.Session.date.desc()
    ).limit(5).all()

    # Roll stats
    r_stats = _roll_stats_for_owner(db, current_user.user_id)

    # Spotlight
    candidates = [t for t in all_techniques if t.proficiency in ("learning", "drilling")]
    spotlight = random.choice(candidates) if candidates else (random.choice(all_techniques) if all_techniques else None)

    return {
        "session_stats": stats,
        "current_rank": {
            "belt": current_rank.belt if current_rank else None,
            "stripes": current_rank.stripes if current_rank else 0,
            "date_awarded": str(current_rank.date_awarded) if current_rank else None,
        },
        "technique_counts": proficiency_counts,
        "total_techniques": len(all_techniques),
        "recent_sessions": [
            {
                "session_id": s.session_id,
                "date": str(s.date),
                "session_type": s.session_type,
                "duration_minutes": s.duration_minutes,
                "focus_area": s.focus_area,
                "attended": s.attended,
            }
            for s in recent_sessions
        ],
        "roll_stats": r_stats,
        "spotlight": {
            "technique_id": spotlight.technique_id,
            "name": spotlight.name,
            "category": spotlight.category,
            "proficiency": spotlight.proficiency,
            "position": spotlight.position,
        } if spotlight else None,
    }
