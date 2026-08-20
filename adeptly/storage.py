import json
import os
import secrets
from datetime import UTC, datetime
from pathlib import Path

ARTIFACT_DIR_ENV = "ARTIFACT_DIR"
LOG_DIR_ENV = "LOG_DIR"
STATES = ("pending", "approved", "rejected")


def artifact_root(override: str | os.PathLike | None = None) -> Path:
    return Path(override or os.getenv(ARTIFACT_DIR_ENV, "out"))


def log_path(override: str | os.PathLike | None = None) -> Path:
    return Path(override or os.getenv(LOG_DIR_ENV, "logs")) / "runs.jsonl"


def new_run_id(now: datetime | None = None) -> str:
    now = now or datetime.now(UTC)
    return now.strftime("%Y%m%d_%H%M%S") + "_" + secrets.token_hex(3)


def run_dir(root: Path, state: str, run_id: str) -> Path:
    if state not in STATES:
        raise ValueError(f"unknown state '{state}'")
    return root / state / run_id


def find_run(root: Path, run_id: str) -> tuple[str, Path] | None:
    for state in STATES:
        d = run_dir(root, state, run_id)
        if (d / "manifest.json").exists():
            return state, d
    return None


def write_manifest(d: Path, manifest: dict) -> Path:
    d.mkdir(parents=True, exist_ok=True)
    p = d / "manifest.json"
    p.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return p


def read_manifest(d: Path) -> dict:
    return json.loads((d / "manifest.json").read_text(encoding="utf-8"))


def append_log(event: dict, path: Path | None = None) -> None:
    p = path or log_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    event = {"ts": datetime.now(UTC).isoformat(timespec="seconds"), **event}
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, sort_keys=True) + "\n")
