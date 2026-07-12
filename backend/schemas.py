"""Back-compat shim: Pydantic contracts live in app.schemas."""
from app.schemas import *  # noqa: F401,F403
from app import schemas as _schemas

__all__ = [name for name in dir(_schemas) if not name.startswith("_")]
