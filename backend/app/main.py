"""Application factory and HTTP middleware."""
import hmac
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import config, migrations
from app.db import Base, engine

load_dotenv(os.path.join(config.BASE_DIR, ".env"))

# Paths reachable without the optional shared API key. Session-token routes
# manage their own auth; the API key only guards what is left (e.g. /oura).
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


def _api_key_required(path: str) -> bool:
    if path in PUBLIC_PATHS or path.startswith("/docs/"):
        return False
    return not path.startswith(SESSION_AUTH_PREFIXES)


@asynccontextmanager
async def _lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    migrations.ensure_backfilled_columns(engine)
    yield


def create_app() -> FastAPI:
    from app.api import all_routers

    app = FastAPI(title="BJJ Tracker API", version="2.0.0", lifespan=_lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins(),
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def require_api_key(request: Request, call_next):
        api_key = config.api_key()
        if not api_key or not _api_key_required(request.url.path):
            return await call_next(request)
        supplied = request.headers.get("x-api-key") or ""
        if not hmac.compare_digest(supplied, api_key):
            return JSONResponse({"detail": "Invalid or missing API key"}, status_code=401)
        return await call_next(request)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    for router in all_routers:
        app.include_router(router)

    return app


app = create_app()
