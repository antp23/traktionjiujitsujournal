"""Deploy/test entrypoint shim.

render.yaml and start.sh run `uvicorn main:app`; the test suite (and any
older tooling) imports `main.app` and the back-fill migration from here.
The real application lives in the `app` package.
"""
from app.db import engine
from app.main import app
from app.migrations import ensure_backfilled_columns

__all__ = ["app", "_ensure_nullable_columns"]


def _ensure_nullable_columns() -> None:
    """Back-compat alias for the startup SQLite column back-fill."""
    ensure_backfilled_columns(engine)
