-- Operational runs for am-ctl. Apply by hand the same way as audit_log.
-- Do not alter audit_log.
-- Retention is 30 days. Run rows age from ended_at. Stage rows age from observed_at.
-- The server deletes older rows and the matching JSONL lines under /opt/agent-zero/oplog/.

CREATE TABLE IF NOT EXISTS operational_runs (
    run_id TEXT PRIMARY KEY,
    action TEXT NOT NULL,
    target TEXT,
    actor TEXT NOT NULL,
    writer_pid INTEGER,
    outcome TEXT,
    started_at TIMESTAMPTZ NOT NULL,
    ended_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS operational_runs_started_at_idx
    ON operational_runs (started_at DESC);

CREATE TABLE IF NOT EXISTS operational_stages (
    id BIGSERIAL PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES operational_runs (run_id) ON DELETE CASCADE,
    stage TEXT NOT NULL,
    phase TEXT NOT NULL,
    severity TEXT NOT NULL,
    body TEXT NOT NULL,
    observed_at TIMESTAMPTZ NOT NULL,
    exit_status INTEGER,
    stdout_tail TEXT,
    stderr_tail TEXT,
    truncated BOOLEAN NOT NULL DEFAULT FALSE,
    cause TEXT,
    instance_present BOOLEAN
);

CREATE INDEX IF NOT EXISTS operational_stages_run_id_idx
    ON operational_stages (run_id, id);
