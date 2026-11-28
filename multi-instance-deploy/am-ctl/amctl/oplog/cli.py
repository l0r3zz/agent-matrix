"""Command line for the decommission script. The script does not assemble JSON."""

import argparse

from amctl.oplog.record import finish_sync, stage_sync, start_run_sync


def _present(value: str | None) -> bool | None:
    if value is None:
        return None
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    raise SystemExit(f"instance-present must be true or false, got {value}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m amctl.oplog")
    sub = parser.add_subparsers(dest="cmd", required=True)

    start = sub.add_parser("start")
    start.add_argument("--action", required=True)
    start.add_argument("--target", default=None)
    start.add_argument("--actor", required=True)

    stage = sub.add_parser("stage")
    stage.add_argument("--run-id", required=True)
    stage.add_argument("--stage", required=True)
    stage.add_argument("--phase", required=True, choices=["start", "finish"])
    stage.add_argument("--severity", default="INFO")
    stage.add_argument("--body", default="")
    stage.add_argument("--cause", default=None)
    stage.add_argument("--exit-status", type=int, default=None)
    stage.add_argument("--stdout", default="")
    stage.add_argument("--stderr", default="")
    stage.add_argument("--instance-present", default=None)

    finish = sub.add_parser("finish")
    finish.add_argument("--run-id", required=True)
    finish.add_argument("--outcome", required=True)
    finish.add_argument("--instance-present", default=None)

    args = parser.parse_args(argv)
    if args.cmd == "start":
        run_id = start_run_sync(action=args.action, target=args.target, actor=args.actor)
        if run_id:
            print(run_id)
        return 0
    if args.cmd == "stage":
        stage_sync(
            run_id=args.run_id,
            stage=args.stage,
            phase=args.phase,
            severity=args.severity,
            body=args.body or f"{args.stage} {args.phase}.",
            cause=args.cause,
            exit_status=args.exit_status,
            stdout=args.stdout,
            stderr=args.stderr,
            instance_present=_present(args.instance_present),
        )
        return 0
    finish_sync(
        run_id=args.run_id,
        outcome=args.outcome,
        instance_present=_present(args.instance_present),
    )
    return 0
