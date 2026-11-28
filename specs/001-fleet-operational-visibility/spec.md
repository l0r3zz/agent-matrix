# Feature Specification: Fleet Operational Visibility

**Feature Branch**: `001-fleet-operational-visibility`

**Created**: 2026-11-27

**Status**: Draft

**Input**: User description: "Spec operational logging so failures can be monitored in a format that OpenTelemetry-based tools can consume. Automation that creates and tears down Agent0 instances must be able to see what happened. The same visibility should cover the agent-matrix ecosystem."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See why instance creation failed (Priority: P1)

An operator or an automation job starts creation of a new Agent0 instance. The job ends, and the terminal where it ran is gone. The operator or a later job can still read that run and tell whether the instance became ready. When it did not, they can see which stage stopped, how long that stage ran, and the cause captured at the time, including the relevant command or service detail. They do not need to reconstruct the failure from container logs before they know where to look.

**Why this priority**: Creation is the path automation will call, and today's result is a short checklist plus one error line. That is enough to name a stage and not enough to diagnose it after the session ends.

**Independent Test**: Start a creation that cannot finish, end the session, then read that run's records. The records name the instance, the failed stage, and the captured cause.

**Acceptance Scenarios**:

1. **Given** a new instance number and a working host, **When** creation finishes successfully, **Then** the run has one outcome of succeeded and one record for each completed stage, and the instance is identified on every record.
2. **Given** creation stops because a required stage does not succeed, **When** the run ends, **Then** the outcome is failed, the failed stage is named, and the record includes the captured cause from that stage.
3. **Given** a creation run that is still in progress, **When** a monitor reads the run, **Then** it can see the stage currently in progress and the stages already completed.
4. **Given** the session that started creation has ended, **When** a later reader asks for that run, **Then** the same outcome and stage records are still available.

---

### User Story 2 - See whether teardown finished (Priority: P2)

An automation job removes an Agent0 instance after a test, a failed creation, or a normal retirement. The job can tell whether removal finished, which step stopped it, and whether the instance is still present. A failed creation followed by teardown is two separate runs, and both remain readable.

**Why this priority**: Spin-up without a visible teardown leaves failed instances behind, and the automation cannot decide whether it is safe to reuse the instance number.

**Independent Test**: Tear down an existing instance, including one left behind by a failed creation, and read the teardown run without watching the original session.

**Acceptance Scenarios**:

1. **Given** an existing instance, **When** teardown finishes, **Then** the run outcome is succeeded and the records show the instance is no longer present.
2. **Given** teardown stops before the instance is gone, **When** the run ends, **Then** the outcome is failed, the stopped step is named, and the record states that the instance may still exist.
3. **Given** a failed creation run for an instance, **When** teardown of that instance runs afterward, **Then** the teardown has its own run identifier and does not alter the creation run's outcome.

---

### User Story 3 - Watch the fleet through one record shape (Priority: P3)

An operator or an external monitor follows the control plane, not only creation and teardown. Health checks, repairs, releases, backups, credential checks, and model changes emit the same kind of record as a creation run. A tool built for OpenTelemetry logs can show these runs without a separate parser for each action.

**Why this priority**: Ecosystem visibility depends on one record shape. Creation and teardown prove the shape. The other control-plane actions reuse it.

**Independent Test**: Perform one health check and one other control-plane change. Both appear as runs with the same required fields as a creation run, and an OpenTelemetry log consumer accepts the records unchanged.

**Acceptance Scenarios**:

1. **Given** any supported control-plane action, **When** the action runs, **Then** it produces a run with an identifier, a target, an action name, stage records, and a terminal outcome.
2. **Given** records from creation, teardown, and at least one other control-plane action, **When** an OpenTelemetry log consumer ingests them, **Then** it retains the severity, time, message, run identifier, action, target, and stage without a custom translator.
3. **Given** two overlapping actions on different instances, **When** a monitor lists runs, **Then** each record belongs to exactly one run and one target.

---

### Edge Cases

- A required stage hangs until its time limit. The failure record names the stage, the limit, and the last observed result. It does not report a blank cause.
- A command produces a very large output. The record keeps a bounded tail of both output streams and says that the tail was truncated.
- A command's output contains an access token, password, or API key. The stored record does not contain that secret.
- An optional step fails and the operation is defined to continue. The run can still succeed, and the optional step is recorded at warning severity rather than as the run's failure.
- The runner is stopped mid-stage. The run has a terminal outcome of failed or interrupted, and the last stage shows that it did not finish.
- Creation is started again for an instance that already has files. The new attempt gets a new run identifier. The earlier run stays unchanged.
- Two creations for different instance numbers overlap. Their records never share a run identifier.
- A reader asks for a run identifier that does not exist. The reader gets an empty result and a clear not-found outcome, not another run's records.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST record every creation, teardown, and other supported control-plane action as one operational run with a unique run identifier, an action name, a target instance when the action has one, a start time, and a terminal outcome of succeeded, failed, or interrupted.
- **FR-002**: The system MUST emit a stage record when a stage starts and when that stage finishes, and those records MUST be readable before the run ends.
- **FR-003**: A failed or interrupted run MUST name the stage that did not finish and MUST include the captured cause: the last observed result for a wait, or the exit status plus a bounded tail of both output streams for a command.
- **FR-004**: A successful creation run MUST record these stages as completed: files prepared (`files_prepared`), containers started (`containers_started`), homeserver ready (`homeserver_ready`), Matrix identity registered (`matrix_identity_registered`), Agent Zero credential derived (`agent_zero_credential_derived`), gateway installed (`gateway_installed`), gateway health confirmed (`gateway_health_confirmed`), and the retired bot confirmed stopped (`retired_bot_stopped`).
- **FR-005**: A successful teardown run MUST record that the instance is no longer present. A failed teardown MUST record the step that stopped and that the instance may still exist.
- **FR-006**: Health checks, repairs, release deployment, backups, credential checks, and model changes MUST use the same run and stage record shape as creation and teardown.
- **FR-007**: Every operational record MUST be expressible as an OpenTelemetry log record, including time, severity, body, attributes, and resource, so an OpenTelemetry log consumer can ingest it without a custom translator.
- **FR-008**: Run and stage records for the same action MUST share one run identifier. Records MUST NOT include access tokens, passwords, or API keys.
- **FR-009**: The system MUST keep each run's records readable after the session that started the run has ended, for at least 30 days.
- **FR-010**: A reader MUST be able to fetch one run by its identifier and list recent runs by target instance and action name.
- **FR-011**: The existing mutation history, which records who changed which durable fleet setting, MUST remain a separate record. An operational run MUST NOT be the only copy of that mutation history, and a mutation history entry MUST NOT be rewritten to pose as an operational run.
- **FR-012**: The system MUST leave message contents, model prompts, and homeserver internals unrecorded except for the result already observed by a control-plane action.

### Key Entities

- **Operational run**: One execution of a control-plane action. Attributes include the run identifier, action name, target instance when applicable, start and end time, outcome, and the actor that started it (an operator or an automation job).
- **Stage record**: One OpenTelemetry log record belonging to a run. Attributes include the stage name, severity, a human-readable body, timing, and, on failure, the captured cause. The resource identifies the control plane and its version.
- **Mutation history entry**: The existing durable record of who changed a fleet setting. It is related to a run only by time and target. It is not a stage record.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In a trial of 10 creation runs with at least 3 forced failures at different stages, a reviewer who was not watching the original session can name the outcome and the failed stage from the run records alone in every case.
- **SC-002**: For every failed run in that trial, the captured cause is specific enough that the reviewer can distinguish a time limit, a refused command, and a rejected registration without opening container logs first.
- **SC-003**: An automation job can start creation, observe the in-progress stage, wait for the terminal outcome, and, on failure, start teardown as a second run. Both run identifiers remain queryable after both jobs exit.
- **SC-004**: An OpenTelemetry log consumer that has no agent-matrix-specific parser accepts 100 percent of the records from creation, teardown, and one other control-plane action, and retains the run identifier, action, target, stage, and severity.
- **SC-005**: A scan of the records from that trial finds zero access tokens, passwords, or API keys.
- **SC-006**: An operator can list the last 20 runs for one instance and open any one of them by identifier in under a minute.

## Assumptions

- This feature covers control-plane actions: instance creation, instance teardown, health checks, repairs, release deployment, backups, credential checks, and model changes. Per-process logs from inside an instance, Matrix message bodies, and model prompts are a later feature.
- "OpenTelemetry-based tools" means a consumer of the OpenTelemetry log data model. This feature does not choose or deploy a collector, dashboard, or storage product. Records must be readable by the automation that started the run and by such a consumer.
- The OpenTelemetry log data model is the required interchange contract. A syslog wire format is not the record this feature authors.
- Teardown means the supported operation that removes one instance. A failed creation does not automatically remove the instance. Automation decides whether to start a teardown run.
- Optional steps that the operation already treats as non-blocking are warnings. They do not by themselves fail the run.
- Stage output stored on a record is bounded. The bound is large enough to include the error and the surrounding lines, and small enough that one command cannot dominate the run record.
- Operational records are retained for 30 days. The mutation history keeps its current retention and purpose.
- Readers of these records are operators and automation on the fleet's control host. This feature does not add a new public audience or a new permission model beyond the control plane's existing access.
- The constitution is `.specify/memory/constitution.md` version 1.2.0. This feature is Principle V.

## Constitution Alignment

This feature satisfies Principles I, III, IV, V, and IX. Creation stays in the provisioner. Teardown stays in `decommission-instance.sh`. Both call one recorder. The target comes from the instance number. Records omit secrets. The records are the diagnosable operations Principle V requires. New recorder and reader behavior has pytest coverage and does not need a live fleet agent.

Principles II, VI, VII, and VIII stay unchanged. This feature does not add a Matrix client, a tool, Rust, or a second crypto store, and it does not log secrets.
