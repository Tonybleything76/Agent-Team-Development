import hashlib
import json
import os
import re
import secrets
from datetime import UTC, datetime
from pathlib import Path

ROOT_ENV = "ADEPTLY_ROOT"
ARTIFACT_DIR_ENV = "ARTIFACT_DIR"
LOG_DIR_ENV = "LOG_DIR"
STATES = ("pending", "approved", "rejected")
MANIFEST_NAME = "manifest.json"
LOCK_NAME = "run.lock"
DEFAULT_ARTIFACT_DIR = "out"
DEFAULT_LOG_DIR = "logs"
RUN_ID_RE = re.compile(r"^\d{8}_\d{6}_[0-9a-f]{6}$")


class StorageError(Exception):
    pass


def base_root() -> Path:
    return Path(os.getenv(ROOT_ENV, "."))


def artifact_root(override: str | os.PathLike | None = None) -> Path:
    if override:
        return Path(override)
    return base_root() / os.getenv(ARTIFACT_DIR_ENV, DEFAULT_ARTIFACT_DIR)


def log_path(override: str | os.PathLike | None = None) -> Path:
    if override:
        return Path(override)
    return base_root() / os.getenv(LOG_DIR_ENV, DEFAULT_LOG_DIR) / "runs.jsonl"


def now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def new_run_id(now: datetime | None = None) -> str:
    now = now or datetime.now(UTC)
    return now.strftime("%Y%m%d_%H%M%S") + "_" + secrets.token_hex(3)


def validate_run_id(run_id: str) -> str:
    """run_id is joined onto a filesystem path; only the generated shape is ever accepted."""
    if not isinstance(run_id, str) or not RUN_ID_RE.match(run_id):
        raise StorageError(f"invalid run_id {run_id!r}")
    return run_id


def run_dir(root: Path, state: str, run_id: str) -> Path:
    if state not in STATES:
        raise ValueError(f"unknown state '{state}'")
    return root / state / validate_run_id(run_id)


def find_run(root: Path, run_id: str) -> tuple[str, Path] | None:
    for state in STATES:
        d = run_dir(root, state, run_id)
        if (d / MANIFEST_NAME).exists():
            return state, d
    return None


def write_manifest(d: Path, manifest: dict) -> Path:
    """Write via temp file + atomic rename so a crash never leaves a half-written manifest.

    The run directory must already exist: never recreate one that a concurrent decision moved.
    """
    if not d.is_dir():
        raise StorageError(f"run directory {d} does not exist")
    final = d / MANIFEST_NAME
    # Unique temp name: two writers to one run directory must not clobber each other's temp file.
    tmp = d / f".{MANIFEST_NAME}.{os.getpid()}.tmp"
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
        f.flush()
        os.fsync(f.fileno())  # a power loss must not leave a zero-length manifest
    os.replace(tmp, final)
    return final


def read_manifest(d: Path) -> dict:
    p = d / MANIFEST_NAME
    try:
        m = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise StorageError(f"unreadable manifest at {p}: {exc}") from exc
    if (
        not isinstance(m, dict)
        or not isinstance(m.get("run_id"), str)
        or not isinstance(m.get("artifacts"), list)
        or any(not isinstance(a, dict) or "role" not in a for a in m["artifacts"])
    ):
        raise StorageError(f"malformed manifest at {p}")
    if m["run_id"] != d.name:
        # Otherwise `pending` prints an id that `show` and `approve` cannot resolve.
        raise StorageError(f"manifest run_id {m['run_id']!r} does not match directory {d.name!r}")
    return m


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def write_lock(d: Path) -> None:
    (d / LOCK_NAME).write_text(str(os.getpid()), encoding="utf-8")


def clear_lock(d: Path) -> None:
    (d / LOCK_NAME).unlink(missing_ok=True)


def lock_holder_alive(d: Path) -> bool:
    """True if a run.lock exists and its pid is still running (the orchestrator is live).

    POSIX only: signal 0 probes existence. PermissionError means the pid exists under another
    user, so it counts as alive. On other platforms the lock file alone is treated as live.
    """
    p = d / LOCK_NAME
    if not p.exists():
        return False
    if os.name != "posix":
        return True
    try:
        pid = int(p.read_text(encoding="utf-8").strip())
    except (ValueError, OSError):
        return False
    if pid <= 0:
        # os.kill(0, 0) signals our own process group and os.kill(-1, 0) signals everything;
        # neither says anything about the orchestrator, so treat both as dead.
        return False
    try:
        os.kill(pid, 0)
    except (ProcessLookupError, OverflowError):
        return False
    except PermissionError:
        return True  # the pid exists, it just belongs to another user
    return True


def append_log(event: dict, path: Path | None = None) -> None:
    p = path or log_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    event = {"ts": now_iso(), **event}
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, sort_keys=True) + "\n")
