"""Database engine and session plumbing.

The engine is created once at import from BJJ_DATABASE_URL / BJJ_SQLITE_PATH,
matching v1's deploy contract (a single SQLite file on a mounted disk).
"""
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app import config

load_dotenv(os.path.join(config.BASE_DIR, ".env"))

DATABASE_URL = config.database_url()

if DATABASE_URL.startswith("sqlite:///"):
    _sqlite_path = DATABASE_URL.replace("sqlite:///", "", 1)
    if _sqlite_path and _sqlite_path != ":memory:":
        os.makedirs(os.path.dirname(os.path.abspath(_sqlite_path)), exist_ok=True)

_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=_connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency yielding a request-scoped session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
