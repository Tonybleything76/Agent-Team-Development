"""Human approval gate.

Nothing an agent produces is 'released' until a named person moves it out of pending/.
The gate records a human decision; it does not authenticate the human (single-operator CLI).
"""

import logging
import os
from pathlib import Path

from .governance import flagged_roles, review_text
from .storage import (
    MANIFEST_NAME,
    StorageError,
    append_log,
    artifact_root,
    find_run,
    lock_holder_alive,
    now_iso,
    read_manifest,
    run_dir,
    sha256_text,
    validate_run_id,
    write_manifest,
)

log = logging.getLogger(__name__)
DECISION_CLAIM = ".deciding"


class GateError(Exception):
    pass


def verify_artifacts(d: Path, manifest: dict) -> None:
    """Check the manifest against the bytes on disk before any decision is recorded.

    Without this, approval attests to a JSON file that anyone can edit: flipping
    `review.ok` to true, or swapping an artifact between `show` and `approve`, would
    otherwise produce a clean approval with no trace.
    """
    for a in manifest.get("artifacts", []):
        if a.get("error"):
            continue
        if not a.get("file"):
            # Every artifact is either a file on disk or a recorded error. Neither means the
            # manifest was edited: clearing `error` alone would otherwise skip verification.
            raise GateError(f"artifact for {a['role']!r} has neither a file nor an error")
        path = d / a["file"]
        if not path.is_file():
            raise GateError(f"artifact {a['file']} is missing; refusing to decide")
        text = path.read_text(encoding="utf-8")
        if a.get("sha256") and sha256_text(text) != a["sha256"]:
            raise GateError(f"artifact {a['file']} changed since the run; re-run before deciding")
        recomputed = review_text(text)
        recorded = (a.get("review") or {}).get("ok")
        if recomputed.ok != bool(recorded):
            raise GateError(
                f"manifest disagrees with {a['file']} (recorded ok={recorded}, "
                f"recomputed ok={recomputed.ok}); refusing to decide"
            )


def list_runs(state: str = "pending", root: Path | None = None) -> list[dict]:
    """Manifests in a state. Corrupt or incomplete run directories are surfaced, not hidden."""
    root = artifact_root(root)
    base = root / state
    if not base.exists():
        return []
    out: list[dict] = []
    for d in sorted(p for p in base.iterdir() if p.is_dir()):
        if not (d / MANIFEST_NAME).exists():
            out.append({"run_id": d.name, "status": "incomplete (no manifest)"})
            continue
        try:
            m = read_manifest(d)
        except StorageError as exc:
            out.append({"run_id": d.name, "status": f"corrupt manifest: {exc}"})
            continue
        if m.get("decision") and m.get("status") != state:
            m = m | {"status": f"{m.get('status')} (decision recorded, move incomplete)"}
        elif state == "pending" and lock_holder_alive(d):
            m = m | {"status": "running (live)"}
        out.append(m)
    return out


def _decide(
    run_id: str,
    decision: str,
    by: str,
    note: str,
    root: Path | None,
    log_file,
    *,
    force: bool = False,
) -> dict:
    if not by or not by.strip():
        raise GateError("a named approver is required (--by)")
    root = artifact_root(root)
    try:
        validate_run_id(run_id)
        found = find_run(root, run_id)
    except StorageError as exc:
        raise GateError(str(exc)) from exc
    if not found:
        orphan = run_dir(root, "pending", run_id)
        if orphan.is_dir() and decision == "rejected" and not lock_holder_alive(orphan):
            # A run that died before its first manifest write: let a human clear it.
            write_manifest(orphan, {"run_id": run_id, "status": "incomplete", "artifacts": []})
            found = ("pending", orphan)
        else:
            raise GateError(f"run '{run_id}' not found under {root}")
    state, src = found
    if state != "pending":
        raise GateError(f"run '{run_id}' is already {state}")
    if lock_holder_alive(src):
        raise GateError(f"run '{run_id}' is still running (live orchestrator); wait for it")
    try:
        manifest = read_manifest(src)
    except StorageError as exc:
        raise GateError(str(exc)) from exc
    verify_artifacts(src, manifest)
    flagged = flagged_roles(manifest.get("artifacts", []))
    if manifest.get("status") in ("running", "incomplete") and decision == "approved":
        raise GateError(f"run '{run_id}' was interrupted before it finished; reject it instead")
    prior = manifest.get("decision")
    if prior:
        # A decision was recorded but the move did not complete. Only the same decision may
        # finish it; a different one is refused so nobody overwrites a recorded decision.
        if prior.get("state") != decision:
            raise GateError(
                f"run '{run_id}' already has a recorded {prior.get('state')} by "
                f"{prior.get('by')}; re-run that command to complete it"
            )
    elif decision == "approved" and flagged and not force:
        raise GateError(f"governance flagged {flagged}; re-run, or approve with --force and a note")
    dst = run_dir(root, decision, run_id)
    if dst.exists():
        raise GateError(f"destination {dst} already exists; refusing to merge directories")
    if not prior:
        try:
            # Whoever creates this wins; the loser gets a clear error instead of both
            # "succeeding" and leaving the directory and the manifest disagreeing.
            os.close(os.open(src / DECISION_CLAIM, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
        except FileExistsError as exc:
            raise GateError(f"run '{run_id}' is being decided by another process") from exc
        entry = {
            "state": decision,
            "by": by.strip(),
            "note": note.strip(),
            "at": now_iso(),
            "forced": bool(force and flagged),
            "flagged_roles": flagged,
        }
        # `decisions` is the append-only history, including anything later superseded by a
        # reopen. `decision` is whichever one is operative now, so existing readers and the
        # rendered report keep working.
        manifest.setdefault("decisions", []).append(entry)
        manifest["decision"] = entry
        manifest["status"] = decision
        # Record the decision in place first, then move: a crash between the two leaves a run in
        # pending/ whose manifest already carries the decision; re-running completes the move.
        write_manifest(src, manifest)
    dst.parent.mkdir(parents=True, exist_ok=True)
    # The dst.exists() check above is the real guard: os.rename onto an existing empty
    # directory succeeds silently on POSIX.
    os.rename(src, dst)
    decided = manifest["decision"]
    append_log(
        {
            "event": decision,
            "run_id": run_id,
            "by": decided["by"],
            "note": decided["note"],
            "forced": decided["forced"],
            "completed_by": by.strip() if prior else None,
        },
        log_file,
    )
    log.info("run %s %s by %s", run_id, decision, decided["by"])
    return manifest


def annotate(run_id: str, by: str, note: str, *, root: Path | None = None, log_file=None) -> dict:
    """Record a comment on a run without deciding it.

    Approve and reject are heavyweight, so without this the only way to register a reservation
    is to reject the whole run — which means mild disagreement goes unsaid. Annotations are
    append-only, allowed in any state, and never change status.
    """
    if not by or not by.strip():
        raise GateError("a named author is required (--by)")
    if not note or not note.strip():
        raise GateError("an annotation needs something to say (--note)")
    root = artifact_root(root)
    try:
        validate_run_id(run_id)
        found = find_run(root, run_id)
    except StorageError as exc:
        raise GateError(str(exc)) from exc
    if not found:
        raise GateError(f"run '{run_id}' not found under {root}")
    state, d = found
    manifest = read_manifest(d)
    entry = {"by": by.strip(), "note": note.strip(), "at": now_iso(), "state_when_written": state}
    manifest.setdefault("annotations", []).append(entry)
    write_manifest(d, manifest)
    append_log(
        {"event": "annotated", "run_id": run_id, "by": entry["by"], "note": entry["note"]}, log_file
    )
    log.info("run %s annotated by %s", run_id, entry["by"])
    return manifest


def reopen(run_id: str, by: str, reason: str, *, root: Path | None = None, log_file=None) -> dict:
    """Take a decided run back to pending, superseding the earlier decision without erasing it.

    A decision you cannot revisit is a decision people avoid making. The history stays
    append-only — the superseded decision remains in `decisions` — so changing your mind is
    cheap and always visible.
    """
    if not by or not by.strip():
        raise GateError("a named person is required (--by)")
    if not reason or not reason.strip():
        raise GateError("a reason is required to reopen")
    root = artifact_root(root)
    try:
        validate_run_id(run_id)
        found = find_run(root, run_id)
    except StorageError as exc:
        raise GateError(str(exc)) from exc
    if not found:
        raise GateError(f"run '{run_id}' not found under {root}")
    state, src = found
    if state == "pending":
        raise GateError(f"run '{run_id}' is already pending; there is no decision to reopen")
    dst = run_dir(root, "pending", run_id)
    if dst.exists():
        raise GateError(f"destination {dst} already exists; refusing to merge directories")
    manifest = read_manifest(src)
    superseded = manifest.get("decision")
    entry = {
        "state": "reopened",
        "by": by.strip(),
        "note": reason.strip(),
        "at": now_iso(),
        "supersedes": {k: superseded.get(k) for k in ("state", "by", "at")} if superseded else None,
    }
    manifest.setdefault("decisions", []).append(entry)
    manifest["decision"] = None  # nothing is operative until someone decides again
    manifest["status"] = "pending"
    write_manifest(src, manifest)
    dst.parent.mkdir(parents=True, exist_ok=True)
    os.rename(src, dst)
    # The old claim marker would otherwise block the next decision on this run.
    (dst / DECISION_CLAIM).unlink(missing_ok=True)
    append_log(
        {
            "event": "reopened",
            "run_id": run_id,
            "by": entry["by"],
            "note": entry["note"],
            "supersedes": entry["supersedes"],
        },
        log_file,
    )
    log.info("run %s reopened by %s", run_id, entry["by"])
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
    return _decide(run_id, "approved", by, note, root, log_file, force=force)


def reject(run_id: str, by: str, reason: str, *, root: Path | None = None, log_file=None) -> dict:
    if not reason or not reason.strip():
        raise GateError("a reason is required to reject")
    return _decide(run_id, "rejected", by, reason, root, log_file)
