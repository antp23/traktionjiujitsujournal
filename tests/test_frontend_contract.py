"""Source-level contract checks pinning the API field names the UI depends on."""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
FRONTEND_SRC = ROOT / "frontend" / "src"
BACKEND = ROOT / "backend"


def _frontend_source():
    return "\n".join(
        path.read_text()
        for path in FRONTEND_SRC.rglob("*.js*")
        if "node_modules" not in path.parts
    )


def test_dashboard_uses_backend_field_names():
    dashboard = (FRONTEND_SRC / "pages" / "Dashboard.jsx").read_text()
    assert "session.session_type" in dashboard
    assert "session.duration_minutes" in dashboard
    assert "parseISO(session.date)" in dashboard
    assert "s.type" not in dashboard
    assert "s.duration}" not in dashboard


def test_frontend_speaks_the_api_contract():
    source = _frontend_source()
    for marker in (
        "/auth/request-link", "/auth/consume-link", "/auth/me",
        "/workspaces/bootstrap", "/workspaces/current", "/workspaces/join",
        "/workspaces/profile", "/sessions", "/techniques", "/rolls",
        "/rank", "/notes", "/goals", "/sharing/threads", "/sharing/inbox",
        "/dashboard", "/oura/status", "/parse",
        "x-session-token", "session_token", "invite_code",
    ):
        assert marker in source, f"frontend no longer references {marker}"


def test_oura_sync_translates_http_errors():
    oura_modules = [
        path for path in BACKEND.rglob("*.py")
        if "daily_readiness" in path.read_text()
    ]
    assert oura_modules, "no backend module implements the Oura sync"
    source = "\n".join(path.read_text() for path in oura_modules)
    assert "TimeoutException" in source
    assert "401" in source
