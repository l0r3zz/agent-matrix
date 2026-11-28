# Contract: Run reader API

The reader is the existing `am-ctl` HTTP server. It uses the existing `X-API-Key` header. It does not add a new permission model.

## List recent runs

`GET /api/v1/runs`

Query parameters:

| Name | Required | Meaning |
|------|----------|---------|
| target | no | Instance name, for example `agent0-6`. |
| action | no | One action name from the data model. |
| limit | no | Default 20. Maximum 100. |

The response is the newest matching runs, each with `run_id`, `action`, `target`, `actor`, `outcome`, `started_at`, and `ended_at`. An open run has a null outcome. The list does not include stage tails.

## Fetch one run

`GET /api/v1/runs/{run_id}`

When the run exists, the response is the run fields plus `stages` in write order. Each stage includes the name, phase, severity, body, time, and any stored cause.

When the run does not exist, the response status is 404 and the body is:

```json
{"outcome": "not_found", "run_id": "<the requested id>", "stages": []}
```

The empty stage list is that run's result. It is not filled from another run.

## What this API does not do

It does not return `audit_log` rows. It does not return message bodies, model prompts, or homeserver internals. It does not accept a write from an outside caller. Writers are the provisioner, the decommission script, and the control-plane services.
