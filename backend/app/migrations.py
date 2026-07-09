"""Idempotent SQLite column back-fills for databases created before the
team/auth era. Runs at startup; each step is a no-op once applied."""
from sqlalchemy.engine import Connection, Engine


def _columns(connection: Connection, table: str) -> set[str]:
    return {
        row[1]
        for row in connection.exec_driver_sql(f"PRAGMA table_info({table})").fetchall()
    }


def ensure_backfilled_columns(engine: Engine) -> None:
    """Add columns that pre-auth-era databases lack, exactly as v1 did."""
    with engine.connect() as connection:
        # notes: v1 ran this unconditionally (the table is assumed to exist).
        if "owner_user_id" not in _columns(connection, "notes"):
            connection.exec_driver_sql("ALTER TABLE notes ADD COLUMN owner_user_id VARCHAR")
            connection.commit()

        for table in ("sessions", "techniques", "roll_logs", "rank_logs"):
            columns = _columns(connection, table)
            if columns and "owner_user_id" not in columns:
                connection.exec_driver_sql(
                    f"ALTER TABLE {table} ADD COLUMN owner_user_id VARCHAR"
                )
                connection.commit()

        share_thread_columns = _columns(connection, "share_threads")
        if share_thread_columns:
            if "status" not in share_thread_columns:
                connection.exec_driver_sql(
                    "ALTER TABLE share_threads "
                    "ADD COLUMN status VARCHAR DEFAULT 'open' NOT NULL"
                )
            if "updated_at" not in share_thread_columns:
                connection.exec_driver_sql(
                    "ALTER TABLE share_threads ADD COLUMN updated_at DATETIME"
                )
                connection.exec_driver_sql(
                    "UPDATE share_threads SET updated_at = created_at WHERE updated_at IS NULL"
                )
            connection.commit()

        thread_message_columns = _columns(connection, "thread_messages")
        if thread_message_columns and "pinned_as_coach_note_id" not in thread_message_columns:
            connection.exec_driver_sql(
                "ALTER TABLE thread_messages ADD COLUMN pinned_as_coach_note_id VARCHAR"
            )
            connection.commit()

        auth_token_columns = _columns(connection, "auth_tokens")
        if auth_token_columns:
            if "expires_at" not in auth_token_columns:
                connection.exec_driver_sql(
                    "ALTER TABLE auth_tokens ADD COLUMN expires_at DATETIME"
                )
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
