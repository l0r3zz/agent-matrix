# Implementation Plan: Fleet Operational Visibility

**Branch**: `001-fleet-operational-visibility` | **Date**: 2026-11-27 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-fleet-operational-visibility/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

Creation, teardown, and the other control-plane actions each become one operational run. Every stage start and stage finish is an OpenTelemetry log record, flushed before the next stage begins, and kept for 30 days after the session that started the run is gone. The same record is written as one OTLP JSON line and as a row in `fleet_ops`, in tables that are not `audit_log`. `am-ctl` reads a run by identifier and lists recent runs by target and action. Secrets are removed before either copy is stored.

## Technical Context

**Language/Version**: Python 3.12 for the recorder, the reader API, and the provisioner. Bash 5.1 for `decommission-instance.sh`, which calls the recorder and does not write records itself.

**Primary Dependencies**: Existing `am-ctl` stack (FastAPI, SQLAlchemy 2, asyncpg, Pydantic, pytest). Add `opentelemetry-api` and `opentelemetry-sdk` at `>=1.27,<2` for the stable logs API. No collector, dashboard, or new database product.

**Storage**: Existing PostgreSQL database `fleet_ops` for the query tables. Append-only OTLP JSON lines under a directory owned by the control-plane user, default `/opt/agent-zero/oplog/`. Both copies share one run identifier. Retention is 30 days.

**Testing**: pytest and pytest-asyncio, using the existing in-memory create_all fixture. Tests do not need a live fleet agent or a homeserver.

**Target Platform**: The fleet control host (g2s), Linux, the same host that runs `am-ctl-server` and `create-instance.sh`.

**Project Type**: Control-plane service plus the existing provision and decommission scripts.

**Performance Goals**: A stage record is readable as soon as that stage starts. An operator can list the last 20 runs for one instance and open one by identifier in under a minute (SC-006).

**Constraints**: Records must not contain access tokens, passwords, or API keys (Principle IV). Each output stream tail is at most 8 KiB. A command failure stores the exit status plus both tails. Mutation history in `audit_log` stays a separate table and is not rewritten. Locked stack versions stay unchanged.

**Scale/Scope**: One control host, instance numbers 1 through 250, eight action names. Overlapping runs on different instances do not share a run identifier.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Result |
|-----------|--------|
| I. Provision through the control plane | Pass. Creation stays in `amctl.provision`. Teardown stays in `decommission-instance.sh`. Both call one recorder. No hand-built triplet and no `finalize-instance.sh`. |
| II. One Matrix client and one crypto store | Pass. Unchanged. The recorder does not open a Matrix client or a crypto store. |
| III. Deterministic identity | Pass. The target is the instance name derived from the instance number. There is no default `agent0-1`. |
| IV. Secrets stay out of records | Pass. Tails are redacted before they are stored or printed. Tests scan fixtures for token and password shapes. |
| V. Diagnosable operations | Pass. This feature is the record Principle V requires. `audit_log` remains the mutation history. |
| VI. Unified tool surface and E2EE | Pass. Unchanged. No tool names and no room-encryption behavior. |
| VII. Rust idioms | Pass. Unchanged. No Rust in this feature. |
| VIII. Security first | Pass. Secrets are not logged. The read API uses the existing `X-API-Key` gate. |
| IX. Test everything | Pass. New modules under `am-ctl` get pytest coverage. Tests do not require a live agent. |
| Locked stack | Pass. Python stays on the 3.12 line. Bash stays 5.1 or newer. No locked version changes. |

No violations. Complexity tracking is empty.

Post-design re-check: the recorder, the JSONL export, the `fleet_ops` tables, and the reader API introduce no second Matrix client, no tool-surface change, no Rust, no locked-version bump, and no write to `audit_log`. The gate still passes.

## Project Structure

### Documentation (this feature)

```text
specs/001-fleet-operational-visibility/
├── plan.md              # This file
├── research.md          # Phase 0
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1
├── contracts/           # Phase 1
│   ├── run-record.md
│   └── runs-api.md
└── tasks.md             # Phase 2, not created by this command
```

### Source Code (repository root)

```text
multi-instance-deploy/am-ctl/
├── amctl/
│   ├── oplog/
│   │   ├── record.py       # start, stage, finish, redact, interrupt sweep
│   │   ├── export.py       # one OTel log record to JSONL and fleet_ops
│   │   └── cli.py          # process entry for the decommission script
│   ├── models/oplog.py
│   ├── routers/runs.py     # GET /api/v1/runs and GET /api/v1/runs/{run_id}
│   ├── provision.py        # creation stages
│   └── services/           # health, repair, release, backup, credentials, models
├── migrations/001_operational_runs.sql
└── tests/test_oplog.py
multi-instance-deploy/scripts/decommission-instance.sh
```

**Structure Decision**: The recorder lives inside `am-ctl` because that process already owns `fleet_ops` and the read API. The provisioner imports it. The decommission script, which is Bash, calls `python -m amctl.oplog` so there is one writer. Tests stay in the existing `am-ctl/tests` tree.

## Complexity Tracking

No constitution violations.
