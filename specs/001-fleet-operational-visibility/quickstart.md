# Quickstart: Fleet Operational Visibility

Validation uses the recorder and the reader. It does not need a live homeserver. The record fields are defined in [contracts/run-record.md](./contracts/run-record.md) and [data-model.md](./data-model.md). The reader paths are defined in [contracts/runs-api.md](./contracts/runs-api.md).

## Prerequisites

- Python 3.12 and the `am-ctl` test extra.
- `opentelemetry-api` and `opentelemetry-sdk` at `>=1.27,<2`.
- The `operational_runs` and `operational_stages` tables, created by the test fixture or by `migrations/001_operational_runs.sql` on a live `fleet_ops`.

## Automated checks

From `multi-instance-deploy/am-ctl`:

```bash
./.venv/bin/python -m pytest tests/test_oplog.py -q
```

Expected:

- A successful create fixture has one run with outcome `succeeded` and a finish record for each required creation stage.
- A failed create fixture names the failed stage and stores the exit status and both tails.
- A tail that contains a bearer token, an `syt_` token, an `sk-or-` key, or a password assignment is stored as `[redacted]`.
- A teardown fixture after a failed create has a different `run_id` and does not change the create outcome.
- A health fixture and a repair fixture use the same fields as the create fixture.
- `GET /api/v1/runs/{missing}` returns 404 with `outcome` `not_found` and an empty `stages` list.
- `GET /api/v1/runs?target=agent0-6&limit=20` returns only that target.
- No row is written to `audit_log` by the recorder.

## Live check after implementation

On the control host, after the SQL migration:

1. Run a create that cannot finish. End the terminal.
2. `am-ctl runs --target agent0-N` shows that run. The outcome is `failed`, the stage is named, and the cause is the captured tail.
3. Run `decommission-instance.sh -y --force N`.
4. The teardown run has its own identifier. The create run's outcome is still `failed`. The teardown outcome is `succeeded` only when the instance directory is gone.
5. Copy one JSONL line into an OpenTelemetry log consumer that has no agent-matrix parser. The line keeps severity, time, body, `run.id`, `run.action`, `run.target`, and `stage.name`.
