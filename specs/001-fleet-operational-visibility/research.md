# Research: Fleet Operational Visibility

## Decision: One recorder writes two copies of the same OpenTelemetry log record

**Decision**: `amctl.oplog` builds an OpenTelemetry log record with `opentelemetry-sdk` (`>=1.27,<2`) and writes it twice before returning: one OTLP JSON line, and one row in `fleet_ops`. Both copies use the same run identifier, time, severity, body, attributes, and resource.

**Rationale**: FR-007 and SC-004 require a consumer to accept the record with no agent-matrix translator. The OTLP JSON line is that record. FR-010 and SC-006 require a lookup by run identifier and a list by target and action in under a minute. The control plane already queries `fleet_ops` for that kind of read. Writing both in one function, and flushing both before the function returns, keeps the in-progress stage visible (FR-002) and keeps the copies from drifting.

**Alternatives considered**: A JSONL file alone makes the 30-day list a scan and makes a single-run lookup a scan. A database row alone is not an OpenTelemetry log record, so a consumer would need a translator. A deployed collector is out of scope; the spec does not choose a collector or a storage product. Hand-built JSON without the SDK can drift from the log data model. The SDK's log record is the model.

## Decision: Query tables are new and are not `audit_log`

**Decision**: Add `operational_runs` and `operational_stages` through SQLAlchemy models. Tests create them with the existing `Base.metadata.create_all` fixture. The live database gets `multi-instance-deploy/am-ctl/migrations/001_operational_runs.sql`, applied by the operator the same way `audit_log` was applied. Alembic is a declared dependency and is unused in this repo. This feature does not start using it.

**Rationale**: FR-011 says the mutation history stays a separate record and must not be rewritten to pose as an operational run. `audit_log` is that history. A new pair of tables keeps the runs queryable without mixing them. A new migration framework would be a second schema path.

**Alternatives considered**: Storing runs inside `audit_log.detail` rewrites the mutation history into the operational record. A second database is a new storage product.

## Decision: The decommission script calls the recorder

**Decision**: `decommission-instance.sh` calls `python -m amctl.oplog` for run start, each teardown stage, and the terminal outcome. It does not assemble JSON.

**Rationale**: Teardown is the supported Bash operation (Principle I). The record shape has to match creation (FR-006). One Python writer is the way to keep the shape, the redaction, and the flush in one place.

**Alternatives considered**: Rewriting decommission in Python changes the operator command the fleet already uses. Echoing JSON from Bash duplicates redaction and can miss a secret.

## Decision: One run per target

**Decision**: A fleet health cycle starts one `health_check` run per agent. A membership repair inside a check starts a separate `repair` run. A fleet-wide backup has a null target and the action name `backup`. Creation and teardown target `agent0-N`.

**Rationale**: US3 scenario 3 says each record belongs to exactly one run and one target. A fleet cycle has many targets, so it cannot be one run. A repair has its own action name (FR-001), so it is not only a stage of the health run.

**Alternatives considered**: One parent run for the fleet cycle would put several targets on one run. Folding a repair into the health run would hide the action name `repair`.

## Decision: Close a killed run on the next server start

**Decision**: Each run stores the writer pid. When `am-ctl-server` starts, a run with no terminal outcome whose pid is not alive on the control host becomes `interrupted`, and its open stage is recorded as unfinished.

**Rationale**: The edge case says a runner stopped mid-stage still has a terminal outcome of failed or interrupted. The provisioner and the decommission script are one-shot processes. They cannot write that outcome if they are killed. The long-running server is the next reader on the same host.

**Alternatives considered**: Leaving the run open forever fails the edge case. A heartbeat from a dead process never arrives, which is the same signal as a dead pid with more moving parts.

## Decision: Redact, then bound both streams

**Decision**: Before a tail is stored or printed, replace bearer tokens, `syt_` tokens, `sk-or-` keys, and any assignment whose name matches password, token, api_key, or secret. Keep at most 8 KiB of stdout and 8 KiB of stderr. Set a truncated flag when either stream was longer.

**Rationale**: FR-003 asks for the exit status and a bounded tail of both streams. FR-008 and Principle IV forbid secrets in the record. The printed command error has to be redacted too, or the terminal becomes a second copy of the secret.

**Alternatives considered**: Storing the full output can keep a token and can let one command dominate the record. Redacting only the database copy leaves the secret in the JSONL line and on the terminal.
