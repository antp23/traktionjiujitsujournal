"""Runtime configuration.

Every environment variable the backend reads lives here. Accessors are
functions (not a cached settings object) because several knobs — dev auth
tokens, SMTP, API key, WhatsApp flags — are legitimately toggled per-process
in tests and ops tooling, and v1 semantics are read-at-use.
"""
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEFAULT_MAGIC_LINK_TTL_MINUTES = 15
DEFAULT_SESSION_TTL_HOURS = 24 * 30
DEFAULT_REQUEST_LIMIT = 5
DEFAULT_REQUEST_WINDOW_MINUTES = 15

QUICK_LOG_DEFAULT_GYM = "Traktion Jiu Jitsu Academy"


def env_str(name: str, default: str | None = None) -> str | None:
    return os.getenv(name, default)


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def env_csv(name: str, default: str) -> list[str]:
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


def cors_origins() -> list[str]:
    return env_csv("BJJ_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")


def api_key() -> str | None:
    return env_str("BJJ_TRACKER_API_KEY")


def frontend_url() -> str:
    return (env_str("BJJ_FRONTEND_URL", "http://localhost:5173") or "").rstrip("/")


def dev_auth_tokens_enabled() -> bool:
    return env_bool("BJJ_DEV_AUTH_TOKENS")


def magic_link_ttl_minutes() -> int:
    return max(1, env_int("BJJ_AUTH_MAGIC_LINK_TTL_MINUTES", DEFAULT_MAGIC_LINK_TTL_MINUTES))


def session_ttl_hours() -> int:
    return max(1, env_int("BJJ_AUTH_SESSION_TTL_HOURS", DEFAULT_SESSION_TTL_HOURS))


def auth_request_limit() -> int:
    return max(1, env_int("BJJ_AUTH_REQUEST_LIMIT", DEFAULT_REQUEST_LIMIT))


def auth_request_window_minutes() -> int:
    return max(1, env_int("BJJ_AUTH_REQUEST_WINDOW_MINUTES", DEFAULT_REQUEST_WINDOW_MINUTES))


def smtp_configured() -> bool:
    return bool(env_str("BJJ_SMTP_HOST") and env_str("BJJ_EMAIL_FROM"))


def whatsapp_capture_enabled() -> bool:
    return (env_str("BJJ_ENABLE_WHATSAPP_CAPTURE", "") or "").lower() == "true"


def meta_verify_token() -> str | None:
    return env_str("BJJ_META_VERIFY_TOKEN")


def meta_app_secret() -> str | None:
    return env_str("BJJ_META_APP_SECRET")


def oura_client_id() -> str | None:
    return env_str("OURA_CLIENT_ID")


def oura_client_secret() -> str | None:
    return env_str("OURA_CLIENT_SECRET")


def oura_redirect_uri() -> str:
    return env_str("OURA_REDIRECT_URI", "http://localhost:8000/oura/callback")


def database_url() -> str:
    default_path = os.path.join(BASE_DIR, "..", "data", "bjj.db")
    sqlite_path = env_str("BJJ_SQLITE_PATH", default_path)
    return env_str("BJJ_DATABASE_URL", f"sqlite:///{sqlite_path}")
