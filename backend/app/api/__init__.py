"""HTTP layer: one module per resource, all registered via `all_routers`."""
from app.api import (
    auth, coaches, dashboard, goals, notes, oura, parse, rank, rolls,
    sessions, sharing, techniques, whatsapp, workspaces,
)

all_routers = [
    sessions.router,
    techniques.router,
    rolls.router,
    rank.router,
    notes.router,
    coaches.router,
    parse.router,
    oura.router,
    auth.router,
    workspaces.router,
    goals.router,
    sharing.router,
    whatsapp.router,
    dashboard.router,
]
