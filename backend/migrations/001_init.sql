-- AgentFlow AI initial schema.
-- Applied automatically by the postgres container on first boot
-- (mounted into /docker-entrypoint-initdb.d). For an existing database, run:
--   psql -U postgres -d agentflow -f backend/migrations/001_init.sql

CREATE TABLE IF NOT EXISTS agent_runs (
    id               TEXT PRIMARY KEY,
    query            TEXT NOT NULL,
    status           TEXT NOT NULL,
    agents_executed  JSONB NOT NULL DEFAULT '[]',
    steps            JSONB NOT NULL DEFAULT '[]',
    evidence         JSONB NOT NULL DEFAULT '{}',
    final_report     TEXT NOT NULL DEFAULT '',
    confidence_score FLOAT NOT NULL DEFAULT 0,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS reports (
    id                TEXT PRIMARY KEY,
    query             TEXT NOT NULL,
    executive_summary TEXT NOT NULL DEFAULT '',
    key_findings      JSONB NOT NULL DEFAULT '[]',
    citations         JSONB NOT NULL DEFAULT '[]',
    confidence_score  FLOAT NOT NULL DEFAULT 0,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS documents (
    id          TEXT PRIMARY KEY,
    filename    TEXT NOT NULL,
    file_type   TEXT NOT NULL DEFAULT '',
    chunk_count INT NOT NULL DEFAULT 0,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_agent_runs_created_at ON agent_runs (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_reports_created_at ON reports (created_at DESC);
