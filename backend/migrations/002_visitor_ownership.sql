-- Per-visitor data separation. Every row records which visitor (browser ID) owns it;
-- the API only ever returns or deletes rows whose owner_id matches the caller.
-- Rows that existed before this migration get owner_id = '' and are therefore
-- invisible to everyone (including the old sample data).

ALTER TABLE documents  ADD COLUMN IF NOT EXISTS owner_id TEXT NOT NULL DEFAULT '';
ALTER TABLE reports    ADD COLUMN IF NOT EXISTS owner_id TEXT NOT NULL DEFAULT '';
ALTER TABLE agent_runs ADD COLUMN IF NOT EXISTS owner_id TEXT NOT NULL DEFAULT '';

CREATE INDEX IF NOT EXISTS idx_documents_owner  ON documents (owner_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_reports_owner    ON reports (owner_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_agent_runs_owner ON agent_runs (owner_id, created_at DESC);
