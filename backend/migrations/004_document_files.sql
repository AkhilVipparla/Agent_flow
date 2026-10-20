-- Original uploaded PDFs, kept so the app can show them back to their owner.
-- Stored in the database (not on disk) so they survive restarts and redeploys on hosts with
-- ephemeral filesystems, and are covered by the same backups as everything else.
-- Rows are removed with their document (ON DELETE CASCADE).

CREATE TABLE IF NOT EXISTS document_files (
    document_id  TEXT PRIMARY KEY REFERENCES documents (id) ON DELETE CASCADE,
    content      BYTEA NOT NULL,
    content_type TEXT NOT NULL DEFAULT 'application/pdf',
    size_bytes   INT NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
