"""Human approval gate.

Nothing an agent produces is 'released' until a named person moves it out of pending/.
The gate records a human decision; it does not authenticate the human (single-operator CLI).
"""

import logging
import shutil
from datetime import UTC, datetime
from pathlib import Path

from .storage import (
    StorageError,
    append_log,
    artifact_root,
    find_run,
    read_manifest,
    run_dir,
    write_manifest,
)

log = logging.getLogger(__name__)


class GateError(Exception):
    pass


def _flagged_roles(manifest: dict) -> list[str]:
    """Roles whose artifact is not governance-APPROVE, including specialists that errored."""
    out = []
    for a in manifest.get("artifacts", []):
        review = a.get("review") or {}
        if a.get("error") or review.get("verdict") != "APPROVE":
            out.append(a["role"])
    return out


def list_runs(state: str = "pending", root: Path | None = None) -> list[dict]:
    """Manifests in a state. Corrupt or incomplete run directories are surfaced, not hidden."""
    root = artifact_root(root)
    base = root / state
    if not base.exists():
        return []
    out: list[dict] = []
    for d in sorted(p for p in base.iterdir() if p.is_dir()):
        stub = {"run_id": d.name, "task": "", "created_at": "", "artifacts": []}
        if not (d / "manifest.json").exists():
            out.append(stub | {"status": "incomplete (no manifest)"})
            continue
        try:
            out.append(read_manifest(d))
        except StorageError as exc:
            out.append(stub | {"status": f"corrupt manifest: {exc}"})
    return out


def _decide(run_id: str, decision: str, by: str, note: str, root: Path | None, log_file) -> dict:
    if not by or not by.strip():
        raise GateError("a named approver is required (--by)")
    root = artifact_root(root)
    try:
        found = find_run(root, run_id)
    except StorageError as exc:
        raise GateError(str(exc)) from exc
    if not found:
        raise GateError(f"run '{run_id}' not found under {root}")
    state, src = found
    if state != "pending":
        raise GateError(f"run '{run_id}' is already {state}")
    manifest = read_manifest(src)
    if manifest.get("status") == "running":
        raise GateError(f"run '{run_id}' is still running or was interrupted; reject it or wait")
    if decision == "approved":
        flagged = _flagged_roles(manifest)
        if flagged and not manifest.get("_force"):
            raise GateError(
                f"governance flagged {flagged}; re-run, or approve with --force and a note"
            )
    dst = run_dir(root, decision, run_id)
    if dst.exists():
        raise GateError(f"destination {dst} already exists; refusing to merge directories")
    manifest.pop("_force", None)
    manifest["decision"] = {
        "state": decision,
        "by": by.strip(),
        "note": note.strip(),
        "at": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    manifest["status"] = decision
    # Record the decision in place first, then move: a crash between the two leaves a run in
    # pending/ whose manifest already carries the decision, and re-running completes the move.
    write_manifest(src, manifest)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst))
    append_log({"event": decision, "run_id": run_id, "by": by.strip(), "note": note}, log_file)
    log.info("run %s %s by %s", run_id, decision, by)
    return manifest


def approve(
    run_id: str,
    by: str,
    note: str = "",
    *,
    force: bool = False,
    root: Path | None = None,
    log_file=None,
) -> dict:
    if force and not note.strip():
        raise GateError("--force requires a --note explaining why")
    if force:
        # Mark intent on the in-memory manifest path: _decide re-reads and honours _force.
        try:
            found = find_run(artifact_root(root), run_id)
        except StorageError as exc:
            raise GateError(str(exc)) from exc
        if found and found[0] == "pending":
            m = read_manifest(found[1])
            m["_force"] = True
            write_manifest(found[1], m)
    return _decide(run_id, "approved", by, note, root, log_file)


def reject(run_id: str, by: str, reason: str, *, root: Path | None = None, log_file=None) -> dict:
    if not reason or not reason.strip():
        raise GateError("a reason is required to reject")
    return _decide(run_id, "rejected", by, reason, root, log_file)
