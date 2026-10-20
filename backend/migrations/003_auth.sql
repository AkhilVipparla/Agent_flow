-- User accounts and login sessions.
-- Passwords are stored only as salted scrypt hashes. Session tokens are stored only as
-- SHA-256 hashes, so a database leak does not hand out usable logins.
-- documents / reports / agent_runs.owner_id (migration 002) now holds app_users.id.

CREATE TABLE IF NOT EXISTS app_users (
    id            TEXT PRIMARY KEY,
    email         TEXT NOT NULL UNIQUE,
    name          TEXT NOT NULL DEFAULT '',
    password_hash TEXT NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS app_sessions (
    token_hash TEXT PRIMARY KEY,
    user_id    TEXT NOT NULL REFERENCES app_users (id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_app_sessions_user    ON app_sessions (user_id);
CREATE INDEX IF NOT EXISTS idx_app_sessions_expires ON app_sessions (expires_at);
