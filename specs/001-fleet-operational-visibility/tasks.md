# Tasks: Fleet Operational Visibility

**Input**: Design documents from `/specs/001-fleet-operational-visibility/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Included. The spec requires pytest coverage for the recorder and the reader, and the tests must not need a live fleet agent.

**Organization**: Tasks are grouped by user story so each story can be implemented and tested on its own.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

Paths are under `multi-instance-deploy/am-ctl/` and `multi-instance-deploy/scripts/`, as in plan.md.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add the logs library and the directory the recorder writes

- [X] T001 [P] Add `opentelemetry-api` and `opentelemetry-sdk` at `>=1.27,<2` to `multi-instance-deploy/am-ctl/pyproject.toml`
- [X] T002 [P] Add `oplog_dir` with default `/opt/agent-zero/oplog/` to `multi-instance-deploy/am-ctl/amctl/config.py`
- [X] T003 [P] Create the `amctl.oplog` package in `multi-instance-deploy/am-ctl/amctl/oplog/__init__.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The run store, the OpenTelemetry record, redaction, and the reader. No user story starts until this phase is complete.

**CRITICAL**: No user story work can begin until this phase is complete

### Tests for the foundation

> Write these tests first. They must fail before T007 through T013.

- [X] T004 [P] Write failing tests in `multi-instance-deploy/am-ctl/tests/test_oplog.py` for redaction, an 8 KiB tail with `truncated` true, a start record readable before the stage finishes, `GET /api/v1/runs/{run_id}` returning 404 with `outcome` `not_found` and `stages` `[]`, and zero new rows in `audit_log`

### Implementation for the foundation

- [X] T005 [P] Create `OperationalRun` and `OperationalStage` in `multi-instance-deploy/am-ctl/amctl/models/oplog.py`. `run_id` is unique text and never reused. `action` is one of `create`, `teardown`, `health_check`, `repair`, `release`, `backup`, `credential_check`, `model_change`. `target` is an instance name or null. `actor` is required. `writer_pid` is the writer process id. `outcome` is null while open, then `succeeded`, `failed`, or `interrupted`. `started_at` is required. `ended_at` is null until the terminal outcome. A stage has required `run_id`, `stage`, `phase` of `start` or `finish`, `severity` of `INFO`, `WARN`, or `ERROR`, one-sentence `body`, and `observed_at`. `stdout_tail` and `stderr_tail` are each at most 8 KiB. `exit_status` is present on a command finish and absent on a wait. `cause` is absent on a clean finish.
- [X] T006 [P] Write the same columns and the 30-day retention note into `multi-instance-deploy/am-ctl/migrations/001_operational_runs.sql`. Do not alter `audit_log`.
- [X] T007 After T006, implement redaction in `multi-instance-deploy/am-ctl/amctl/oplog/record.py`. Replace a bearer token, a value that starts with `syt_` or `sk-or-`, and an assignment whose name contains `password`, `token`, `api_key`, or `secret` with `[redacted]`. Apply that filter before a tail is stored and before it is printed. Keep at most 8 KiB of stdout and 8 KiB of stderr, and set `truncated` true when either stream was cut.
- [X] T008 After T006, implement `multi-instance-deploy/am-ctl/amctl/oplog/export.py` so one call writes one OpenTelemetry log record as an OTLP JSON line under `oplog_dir` and the matching `operational_stages` row, then flushes both before returning. Resource attributes are `service.name` `am-ctl` and `service.version` of the running am-ctl version. Attributes are `run.id`, `run.action`, `run.target` when present, `stage.name`, and `stage.phase`.
- [X] T009 Implement `start`, `stage`, and `finish` in `multi-instance-deploy/am-ctl/amctl/oplog/record.py`. `start` inserts `operational_runs` with a new `run_id`, the action, the target or null, the actor, `writer_pid`, null `outcome`, and `started_at`. A stage `start` is flushed before the stage work begins. `finish` sets `outcome` to `succeeded`, `failed`, or `interrupted` and sets `ended_at`. A second run for the same target inserts a new row and does not update the earlier row.
- [X] T010 Mark a run `interrupted` from `multi-instance-deploy/am-ctl/amctl/oplog/record.py` when `outcome` is null and `writer_pid` is not alive on the control host, and record the open stage as unfinished
- [X] T011 Delete `operational_runs` and `operational_stages` rows, and their JSONL lines, older than 30 days in `multi-instance-deploy/am-ctl/amctl/oplog/record.py`. Run rows age from `ended_at`. Stage rows age from `observed_at`.
- [X] T012 [P] Implement `GET /api/v1/runs` and `GET /api/v1/runs/{run_id}` in `multi-instance-deploy/am-ctl/amctl/routers/runs.py` behind the existing `X-API-Key` gate. The list accepts `target`, `action`, and `limit` (default 20, maximum 100) and returns newest runs without tails. A known run returns its stages in write order, and each stage includes `observed_at`. Duration is the finish `observed_at` minus the start `observed_at`. An unknown `run_id` returns 404 with `outcome` `not_found` and `stages` `[]`.
- [X] T013 Register the runs router in `multi-instance-deploy/am-ctl/amctl/app.py` and, on server start, run the interrupt sweep and the 30-day delete

**Checkpoint**: A caller can open a run, flush a stage, finish it, and read it back. User stories can start.

---

## Phase 3: User Story 1 - See why instance creation failed (Priority: P1)

**Goal**: After creation ends, a later reader can see the outcome, the stage that stopped, and the captured cause.

**Independent Test**: Start a creation that cannot finish, end the session, then read that run. The records name the instance, the failed stage, and the captured cause.

### Tests for User Story 1

> Write these tests first. They must fail before T015.

- [X] T014 [US1] Add failing create tests to `multi-instance-deploy/am-ctl/tests/test_oplog.py`. A successful create has outcome `succeeded` and a finish record for `files_prepared`, `containers_started`, `homeserver_ready`, `matrix_identity_registered`, `agent_zero_credential_derived`, `gateway_installed`, `gateway_health_confirmed`, and `retired_bot_stopped`, and every record names the instance. A failed create names the failed stage and stores the exit status plus both tails, or the time limit and the last observed result for a wait. A failed `matrix_identity_registered` stage stores the registration error as its cause. A start record is readable while the run is open. A second create for the same instance gets a new `run_id` and leaves the earlier outcome unchanged. Two overlapping creates use two `run_id` values.

### Implementation for User Story 1

- [X] T015 [US1] Record those eight stages from `provision_agent` and `bring_up` in `multi-instance-deploy/am-ctl/amctl/provision.py`, plus a certificate stage that finishes at `WARN` when the step CLI is absent and does not fail the run. The target is the instance name from the instance number. There is no default `agent0-1`.
- [X] T016 [US1] When a wait in `multi-instance-deploy/am-ctl/amctl/provision.py` reaches its time limit, store the stage name, the limit, and the last observed result. Do not store a blank cause.
- [X] T017 [US1] Add `am-ctl runs` list and show to `multi-instance-deploy/am-ctl/amctl_cli/cli.py`, calling `GET /api/v1/runs` and `GET /api/v1/runs/{run_id}`

**Checkpoint**: User Story 1 can be tested without teardown or the other control-plane actions.

---

## Phase 4: User Story 2 - See whether teardown finished (Priority: P2)

**Goal**: Teardown is its own run. The reader can see whether the instance directory is gone.

**Independent Test**: Tear down an instance left by a failed create and read the teardown run without the original session. The create outcome is unchanged.

### Tests for User Story 2

> Write this test first. It must fail before T020.

- [X] T018 [US2] Add failing teardown tests to `multi-instance-deploy/am-ctl/tests/test_oplog.py`. A finished teardown has outcome `succeeded`, stages `containers_removed` and `directory_removed`, and `instance.present` false. A stopped teardown has outcome `failed`, names the stopped step, and says the instance may still exist. The teardown `run_id` differs from the create `run_id`, and the create outcome stays `failed`.

### Implementation for User Story 2

- [X] T019 [US2] Implement `python -m amctl.oplog` through `multi-instance-deploy/am-ctl/amctl/oplog/__main__.py` and `multi-instance-deploy/am-ctl/amctl/oplog/cli.py` with start, stage, and finish commands. The script does not assemble JSON.
- [X] T020 [US2] Call that module from `multi-instance-deploy/scripts/decommission-instance.sh` around container removal and `remove_instance_dir`. On success, record `instance.present` false. On failure, record the stopped step and that the instance may still exist. Do not change the create run.

**Checkpoint**: User Stories 1 and 2 both work on their own.

---

## Phase 5: User Story 3 - Watch the fleet through one record shape (Priority: P3)

**Goal**: Health checks, repairs, releases, backups, credential checks, and model changes use the same run and stage records as creation.

**Independent Test**: Run one health check and one other control-plane action. Both runs have the same required fields as a create run, and an OpenTelemetry log consumer accepts the JSONL line unchanged.

### Tests for User Story 3

> Write this test first. It must fail before T022.

- [X] T021 [US3] Add failing tests to `multi-instance-deploy/am-ctl/tests/test_oplog.py` that a `health_check` run and a `repair` run each have `run.id`, `run.action`, `run.target` when the action has one instance, `stage.name`, severity, time, and body, and that the JSONL resource is `service.name` `am-ctl`. A fleet health cycle creates one run per agent. A backup run has a null target. Stage bodies do not contain message contents, model prompts, or homeserver internals.

### Implementation for User Story 3

- [X] T022 [P] [US3] Open one `health_check` run per agent inside `run_agent_health_checks` in `multi-instance-deploy/am-ctl/amctl/services/health_engine.py`
- [X] T023 [P] [US3] Open a separate `repair` run from `apply_agent_reconciliation` in `multi-instance-deploy/am-ctl/amctl/services/reconciler.py` and from `repair_room_membership` in `multi-instance-deploy/am-ctl/amctl/services/matrix.py`
- [X] T024 [P] [US3] Open a `release` run from `deploy_release_to_agent` in `multi-instance-deploy/am-ctl/amctl/services/deployer.py`
- [X] T025 [P] [US3] Open a `backup` run with a null target from `execute_backup_suite` in `multi-instance-deploy/am-ctl/amctl/services/backup.py`
- [X] T026 [P] [US3] Open a `credential_check` run from `verify_agent_credentials` in `multi-instance-deploy/am-ctl/amctl/routers/credentials.py`
- [X] T027 [P] [US3] Open a `model_change` run from `set_agent_model_config` in `multi-instance-deploy/am-ctl/amctl/services/model_manager.py`. Record the result only, not the model prompt.

**Checkpoint**: All three stories work on their own.

---

## Phase 6: Polish and Cross-Cutting Concerns

**Purpose**: Operator documentation and the quickstart check

- [X] T028 [P] Document `GET /api/v1/runs`, the default directory `/opt/agent-zero/oplog/`, and the 30-day retention in `docs/operations-manual.md`
- [X] T029 Run the automated quickstart check from `specs/001-fleet-operational-visibility/quickstart.md` with `pytest tests/test_oplog.py` in `multi-instance-deploy/am-ctl`

---

## Dependencies and Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies. Start immediately.
- **Foundational (Phase 2)**: Depends on Setup. Blocks every user story.
- **User Stories (Phase 3, Phase 4, Phase 5)**: Depend on Foundational. They do not depend on each other.
- **Polish (Phase 6)**: Depends on the user stories that are in scope.

### User Story Dependencies

- **User Story 1 (P1)**: Starts after Foundational. No dependency on US2 or US3.
- **User Story 2 (P2)**: Starts after Foundational. Uses the same recorder as US1 and does not change a create run.
- **User Story 3 (P3)**: Starts after Foundational. Uses the same recorder and reader. It does not require a create or a teardown run.

### Within Each User Story

- Tests are written and fail before the story implementation.
- The recorder exists before a story calls it.
- The reader exists before the CLI calls it.

### Parallel Opportunities

- T001, T002, and T003 can run together.
- T004, T005, and T006 can run together. T007 and T008 can run together after T006. T012 can run with T009 through T011.
- After Foundational, US1, US2, and US3 can run together.
- T022 through T027 can run together.

---

## Parallel Example: User Story 3

```bash
Task: "Open one health_check run per agent in multi-instance-deploy/am-ctl/amctl/services/health_engine.py"
Task: "Open a repair run in multi-instance-deploy/am-ctl/amctl/services/reconciler.py and matrix.py"
Task: "Open a release run in multi-instance-deploy/am-ctl/amctl/services/deployer.py"
Task: "Open a backup run in multi-instance-deploy/am-ctl/amctl/services/backup.py"
Task: "Open a credential_check run in multi-instance-deploy/am-ctl/amctl/routers/credentials.py"
Task: "Open a model_change run in multi-instance-deploy/am-ctl/amctl/services/model_manager.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1.
2. Complete Phase 2.
3. Complete Phase 3.
4. Stop and run the User Story 1 tests in `tests/test_oplog.py`.

### Incremental Delivery

1. Setup and Foundational make a run readable.
2. User Story 1 makes creation diagnosable after the session ends.
3. User Story 2 makes teardown a second run.
4. User Story 3 gives the other control-plane actions the same record shape.

### Parallel Team Strategy

1. Finish Setup and Foundational together.
2. Then one person can take creation, one teardown, and one the other control-plane actions.

---

## Notes

- [P] tasks use different files and do not wait on each other.
- Story labels map a task to US1, US2, or US3.
- Each story is completable without the later stories.
- Write the story tests so they fail before the story implementation.
- Do not write operational runs into `audit_log`.
