"""Write one OpenTelemetry log record as one OTLP JSON line."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from opentelemetry._logs import LogRecord, SeverityNumber
from opentelemetry.sdk._logs import ReadableLogRecord
from opentelemetry.sdk.resources import Resource

from amctl import __version__
from amctl.config import settings

_SEVERITY = {
    "INFO": SeverityNumber.INFO,
    "WARN": SeverityNumber.WARN,
    "ERROR": SeverityNumber.ERROR,
}


def _nanos(when: datetime) -> int:
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    return int(when.timestamp() * 1_000_000_000)


def _otlp_value(value):
    if isinstance(value, bool):
        return {"boolValue": value}
    if isinstance(value, int):
        return {"intValue": str(value)}
    return {"stringValue": str(value)}


def _attributes(items: dict) -> list[dict]:
    return [{"key": key, "value": _otlp_value(value)} for key, value in items.items()]


def _line(body: str, severity: str, when: datetime, attributes: dict) -> dict:
    resource = Resource.create(
        {
            "service.name": "am-ctl",
            "service.version": __version__,
        }
    )
    record = LogRecord(
        timestamp=_nanos(when),
        observed_timestamp=_nanos(when),
        severity_text=severity,
        severity_number=_SEVERITY[severity],
        body=body,
        attributes=attributes,
    )
    readable = ReadableLogRecord(record, resource)
    log_attributes = dict(readable.log_record.attributes or {})
    return {
        "resourceLogs": [
            {
                "resource": {"attributes": _attributes(dict(readable.resource.attributes))},
                "scopeLogs": [
                    {
                        "scope": {"name": "amctl.oplog"},
                        "logRecords": [
                            {
                                "timeUnixNano": str(readable.log_record.timestamp),
                                "observedTimeUnixNano": str(readable.log_record.observed_timestamp),
                                "severityText": readable.log_record.severity_text,
                                "body": {"stringValue": str(readable.log_record.body)},
                                "attributes": _attributes(log_attributes),
                            }
                        ],
                    }
                ],
            }
        ]
    }


def log_path() -> Path:
    return Path(settings.oplog_dir) / "oplog.jsonl"


def append(payload: dict) -> None:
    """Flush one JSON line to disk before the caller returns."""
    path = log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(payload, separators=(",", ":"), default=str) + "\n"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line)
        handle.flush()
        os.fsync(handle.fileno())


def write_stage(stage, run) -> None:
    attributes = {
        "run.id": run.run_id,
        "run.action": run.action,
        "stage.name": stage.stage,
        "stage.phase": stage.phase,
    }
    if run.target:
        attributes["run.target"] = run.target
    if run.outcome:
        attributes["run.outcome"] = run.outcome
    if stage.exit_status is not None:
        attributes["cause.exit_status"] = stage.exit_status
    if stage.stdout_tail:
        attributes["cause.stdout_tail"] = stage.stdout_tail
    if stage.stderr_tail:
        attributes["cause.stderr_tail"] = stage.stderr_tail
    if stage.truncated:
        attributes["cause.truncated"] = True
    if stage.cause and stage.exit_status is None:
        attributes["cause.last_result"] = stage.cause
    if stage.instance_present is not None:
        attributes["instance.present"] = stage.instance_present
    append(_line(stage.body, stage.severity, stage.observed_at, attributes))


def write_terminal(run, when: datetime, instance_present: bool | None) -> None:
    severity = "ERROR" if run.outcome in {"failed", "interrupted"} else "INFO"
    attributes = {
        "run.id": run.run_id,
        "run.action": run.action,
        "run.outcome": run.outcome,
        "stage.name": "run",
        "stage.phase": "finish",
    }
    if run.target:
        attributes["run.target"] = run.target
    if instance_present is not None:
        attributes["instance.present"] = instance_present
    body = f"The run {run.outcome}."
    append(_line(body, severity, when, attributes))
