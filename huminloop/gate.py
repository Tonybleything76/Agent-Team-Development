"""Human approval gate.

Nothing an agent produces is 'released' until a named person moves it out of pending/.
The gate records a human decision; it does not authenticate the human (single-operator CLI).
"""

import logging
import os
from pathlib import Path

from .governance import flagged_roles, review_text
from .orchestrator import CRITIC_ROLE, SYNTHESIS_ROLE
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


# ---------------------------------------------------------------------------
# The `status` contract: one answer to "what does this run need right now".
#
# Five surfaces (`pending`, `show`, `render`, `serve`, and the gate itself) each worked this
# out for themselves, which is five chances to disagree. The approved design doc proposed the
# shape below as a first cut and left the exact enums to implementation; they are settled here.
#
# `reject` is the one addition to the doc's four-value `pending_action`. Without it an
# interrupted run reports `approve`, and `approve` then refuses it — the command would be
# handing out an answer the very next command contradicts, which is the failure this exists to
# end. Reject is that run's only legal move, so the enum says so.
# ---------------------------------------------------------------------------
RUN_STATUSES = ("running", "pending", "approved", "rejected")
PENDING_ACTIONS = ("wait", "resynthesize", "approve", "reject", "done")
# Statuses a manifest carries when a run died before it finished. The directory still says
# pending; nothing is alive; approve refuses it by name.
INTERRUPTED_STATUSES = ("running", "incomplete")
_DECISION_ACTION = {"approved": "approve", "rejected": "reject"}


def _status_response(run_id: str, **fields) -> dict:
    """Every `status` answer, built from one place so the shape cannot diverge.

    The function had two return statements; a later commit added two fields to one of them and
    not the other, so a caller reading `artifacts_verified` on a run that died before its first
    manifest write got a KeyError — from the command whose whole purpose is being the one shape
    a caller can rely on. Defaults here are the answer for a run we know nothing about.

    Every default that asserts something is the cautious value. The first version defaulted
    `artifacts_verified` to True, so any path that did not override it — a run with no
    manifest, a run still being written, a decided run — claimed a check nobody ran. An
    approved deliverable edited after approval reported itself verified. The field is now true
    only when a check actually ran and passed.
    """
    return {
        "run_id": run_id,
        "status": "pending",
        "needs_resynthesize": False,
        "flagged_roles": [],
        "unrevised_roles": [],
        "interrupted": False,
        "artifacts_verified": False,
        "verification_error": "not verified",
        "pending_action": "approve",
    } | fields


def status(run_id: str, root: Path | None = None) -> dict:
    """What this run needs right now, as recorded fact rather than caller inference.

    `needs_resynthesize` is narrow on purpose: it is true exactly when `resynthesize` would
    both be accepted and be the thing to do — pattern (a), the Engagement Lead's own synthesis
    call coming back empty. It mirrors that function's preconditions rather than guessing at
    them, so "the status command said yes and the command then refused" cannot happen.

    `unrevised_roles` is pattern (b): a specialist's *critic* call returned empty, so that
    artifact was never challenged and never revised. There is no recovery command for it. The
    two are reported separately and never merged — claiming `resynthesize` covers pattern (b)
    would offer a fix that does nothing. Today pattern (b) is otherwise invisible: such an
    artifact has no error, no process flags, and a clean review, so `flagged_roles` never
    mentions it.

    `flagged_roles` and `needs_resynthesize` are independent and can both be set: a flagged run
    is one a human must look at, not one that is blocked from reaching approval.

    Raises rather than inventing a state: an unknown run_id or an unreadable manifest is an
    error to surface, never something a caller should wait out.
    """
    root = artifact_root(root)
    try:
        validate_run_id(run_id)
        found = find_run(root, run_id)
    except StorageError as exc:
        raise GateError(str(exc)) from exc
    if not found:
        orphan = run_dir(root, "pending", run_id)
        if orphan.is_dir():
            # `list_runs` surfaces this as "incomplete (no manifest)", so denying it here
            # would put the two gate surfaces into exactly the disagreement this command
            # exists to end. It died before its first manifest write; a human clears it.
            alive = lock_holder_alive(orphan)
            return _status_response(
                run_id,
                status="running" if alive else "pending",
                interrupted=not alive,
                verification_error="no manifest was written, so there is nothing to verify against",
                pending_action="wait" if alive else "reject",
            )
        raise GateError(f"run '{run_id}' not found under {root}")
    state, d = found
    try:
        manifest = read_manifest(d)
    except StorageError as exc:
        raise GateError(str(exc)) from exc

    artifacts = manifest.get("artifacts") or []
    live = lock_holder_alive(d)
    recorded = str(manifest.get("status") or "")
    interrupted = state == "pending" and not live and recorded in INTERRUPTED_STATUSES

    lead_succeeded = any(a.get("role") == SYNTHESIS_ROLE and not a.get("error") for a in artifacts)
    # Excludes the lead, exactly as resynthesize() does before deciding it has something to work
    # from: a lead artifact is what it produces, never an input to producing one.
    specialists_survived = any(
        not a.get("error") for a in artifacts if a.get("role") != SYNTHESIS_ROLE
    )
    needs_resynthesize = bool(
        state == "pending" and not live and not lead_succeeded and specialists_survived
    )

    # Only meaningful when this run critiqued at all: --no-critique leaves every artifact
    # without one, and that is a choice the operator made, not a critic that failed.
    critiqued = any(a.get("critique") for a in artifacts)
    unrevised_roles = [
        a["role"]
        for a in artifacts
        if critiqued
        and not a.get("error")
        and not a.get("critique")
        and a.get("role") != CRITIC_ROLE  # the critic is never its own critic
    ]

    # The bytes, checked the same way `_decide` checks them. Recommending "approve" for a run
    # whose artifact was edited since it ran is the command contradicting the very next
    # command — the failure `pending_action` exists to prevent, and one this branch already
    # fixed for interrupted runs and missed here.
    # Every settled run, decided ones included: an approved deliverable edited after approval is
    # precisely what this record exists to reveal. A run still being written cannot be checked
    # yet, and says so rather than borrowing a result.
    if live:
        verified, verify_error = False, "run is still in progress; artifacts cannot be checked yet"
    else:
        try:
            verify_artifacts(d, manifest)
            verified, verify_error = True, ""
        except GateError as exc:
            verified, verify_error = False, str(exc)

    decision = manifest.get("decision") or {}
    if state in ("approved", "rejected"):
        action = "done"
    elif live:
        action = "wait"
    elif decision.get("state") in _DECISION_ACTION:
        # A decision is recorded but the move did not complete; re-running that same command
        # finishes it, and no other decision is allowed to.
        action = _DECISION_ACTION[decision["state"]]
    elif needs_resynthesize:
        action = "resynthesize"
    elif interrupted or not verified:
        # A tampered run cannot be approved and cannot be repaired by resynthesizing; the only
        # move the gate will accept is rejecting it and running again.
        action = "reject"
    else:
        action = "approve"

    return _status_response(
        manifest["run_id"],
        status="running" if live else state,
        needs_resynthesize=needs_resynthesize,
        flagged_roles=flagged_roles(artifacts),
        unrevised_roles=unrevised_roles,
        interrupted=interrupted,
        # Empty when the bytes match the manifest. Named rather than folded into
        # `flagged_roles`, which is about what the team produced, not about tampering.
        artifacts_verified=verified,
        verification_error=verify_error,
        pending_action=action,
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
