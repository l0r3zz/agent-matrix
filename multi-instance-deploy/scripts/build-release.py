#!/usr/bin/env python3
"""Deterministic, reproducible release bundle builder for am-ctl (Phase 9).

Packages all tracked Phase 1-8 fleet artifacts with normalized tar headers
(mtime=0, uid=0, gid=0, uname='root', gname='root') and gzip mtime=0 so two
builds of the same source artifacts produce byte-for-byte identical tarballs
and SHA-256 checksums. Also scans all packaged files to guarantee zero secrets.
"""

import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import tarfile

REPO_DIR = Path(__file__).resolve().parent.parent

ARTIFACTS = [
    ("matrix-bot-rust", REPO_DIR / "templates/matrix-bot/matrix-bot-rust", 0o755),
    ("run-bot-wrapper.sh", REPO_DIR / "templates/matrix-bot/run-bot-wrapper.sh", 0o755),
    ("run-matrix-bot.sh", REPO_DIR / "templates/matrix-bot/run-matrix-bot.sh", 0o755),
    ("derive-a0-token.sh", REPO_DIR / "templates/scripts/derive-a0-token.sh", 0o755),
    ("preflight-check.sh", REPO_DIR / "templates/scripts/preflight-check.sh", 0o755),
    ("watchdog.sh", REPO_DIR / "templates/scripts/watchdog.sh", 0o755),
    ("startup-services.sh", REPO_DIR / "templates/scripts/startup-services.sh", 0o755),
]

SECRET_PATTERNS = [
    re.compile(rb"syt_[A-Za-z0-9_]+"),
    re.compile(rb"^A0_API_KEY=.+", re.MULTILINE),
]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_deterministic_bundle(version: str, output_path: Path) -> str:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    artifact_hashes: dict[str, str] = {}
    sha256sums_lines: list[str] = []
    files_payload: list[tuple[str, bytes, int]] = []

    for name, src_path, mode in sorted(ARTIFACTS, key=lambda x: x[0]):
        if not src_path.is_file():
            raise FileNotFoundError(f"Missing required release artifact: {src_path}")
        raw = src_path.read_bytes()

        # Verify no secrets in text/script artifacts
        if name.endswith(".sh"):
            for pat in SECRET_PATTERNS:
                if pat.search(raw):
                    raise ValueError(f"Secret pattern {pat.pattern!r} detected in {name}!")

        full_hash = sha256_bytes(raw)
        artifact_hashes[name] = full_hash[:12]
        sha256sums_lines.append(f"{full_hash}  {name}")
        files_payload.append((name, raw, mode))

    manifest_bytes = (
        json.dumps(
            {"version": version, "artifact_hashes": dict(sorted(artifact_hashes.items()))},
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode()
    sha256sums_bytes = ("\n".join(sha256sums_lines) + "\n").encode()

    files_payload.append(("MANIFEST.json", manifest_bytes, 0o644))
    files_payload.append(("SHA256SUMS", sha256sums_bytes, 0o644))

    tar_buf = io.BytesIO()
    with tarfile.open(fileobj=tar_buf, mode="w", format=tarfile.PAX_FORMAT) as tf:
        for name, data, mode in sorted(files_payload, key=lambda x: x[0]):
            info = tarfile.TarInfo(name=name)
            info.size = len(data)
            info.mtime = 0
            info.mode = mode
            info.uid = 0
            info.gid = 0
            info.uname = "root"
            info.gname = "root"
            tf.addfile(info, io.BytesIO(data))

    tar_bytes = tar_buf.getvalue()
    with output_path.open("wb") as raw_f:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw_f, mtime=0) as gz_f:
            gz_f.write(tar_bytes)

    bundle_hash = sha256_bytes(output_path.read_bytes())
    return bundle_hash


def main() -> None:
    parser = argparse.ArgumentParser(description="Build deterministic am-ctl release bundle")
    parser.add_argument("--version", required=True, help="Release version (e.g. v1.2.0)")
    parser.add_argument("--output", required=True, help="Output .tar.gz path")
    args = parser.parse_args()

    out = Path(args.output)
    digest = build_deterministic_bundle(args.version, out)
    print(f"Built {out} (sha256={digest})")


if __name__ == "__main__":
    main()
