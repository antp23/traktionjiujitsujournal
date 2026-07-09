"""Back-compat shim: the engine and session plumbing live in app.db."""
from app.db import Base, DATABASE_URL, SessionLocal, engine, get_db

__all__ = ["Base", "DATABASE_URL", "SessionLocal", "engine", "get_db"]
