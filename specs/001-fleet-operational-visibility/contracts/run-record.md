# Contract: Operational log record

Each stage start, stage finish, and terminal outcome is one OpenTelemetry log record. The JSONL file stores that record as one OTLP JSON object per line. The database row stores the same fields. A consumer reads the JSONL line and does not need an agent-matrix parser.

## Resource

| Attribute | Value |
|-----------|-------|
| service.name | `am-ctl` |
| service.version | The running `am-ctl` version |

## Attributes

| Attribute | Required | Meaning |
|-----------|----------|---------|
| run.id | yes | Run identifier. |
| run.action | yes | Action name from the data model. |
| run.target | no | Instance name. Omitted when the action has no single instance. |
| run.outcome | terminal record only | `succeeded`, `failed`, or `interrupted`. |
| stage.name | yes | Stage name. The terminal record uses `run`. |
| stage.phase | yes | `start` or `finish`. |
| cause.exit_status | command failure | Process exit status. |
| cause.stdout_tail | command failure | Redacted stdout, at most 8 KiB. |
| cause.stderr_tail | command failure | Redacted stderr, at most 8 KiB. |
| cause.truncated | when cut | `true` when a tail was shortened. |
| cause.last_result | wait failure | Last observed result and the time limit. |
| instance.present | teardown terminal record | `true` or `false`. |

## Severity

| Event | Severity |
|-------|----------|
| Stage start, clean finish, success outcome | INFO |
| Optional step the operation continues after | WARN |
| Failed stage, failed outcome, interrupted outcome | ERROR |

## Redaction

Before a tail or a body is written, replace:

- a bearer token
- a value that starts with `syt_` or `sk-or-`
- an assignment whose name contains `password`, `token`, `api_key`, or `secret`, in any letter case

The replacement text is `[redacted]`. The same filter applies to the line printed on the terminal.

## Read behavior the record must support

- A start record is on disk and in `fleet_ops` before the stage's work begins.
- Records for one run share one `run.id`.
- Two overlapping actions use two `run.id` values.
- A reader that asks for an unknown `run.id` gets no records from any other run.
