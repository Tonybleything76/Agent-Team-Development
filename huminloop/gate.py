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
# A reject superseding a recorded approval cannot take DECISION_CLAIM: that approval already
# holds it. Without a claim of its own, two supersedes both wrote the manifest and one was lost.
SUPERSEDE_CLAIM = ".superseding"


class GateError(Exception):
    pass


# The only states a recorded-but-unmoved decision can hold, and the command that completes
# each. `reopen` sets `decision` to None, so "reopened" is never operative; anything else in
# `decision.state` is an edit.
_DECISION_ACTION = {"approved": "approve", "rejected": "reject"}


def _is_decision(value: object) -> bool:
    # Every decision the gate writes names who made it and when. One without them is not a
    # human decision, and completing it would move a run with no named approver.
    return (
        isinstance(value, dict)
        and isinstance(value.get("state"), str)
        and value["state"] in _DECISION_ACTION
        and all(isinstance(value.get(k), str) and value[k].strip() for k in ("by", "at"))
        and isinstance(value.get("note"), str | None)
    )


def recorded_decision(manifest: dict) -> dict | None:
    """The recorded decision the gate may complete, or None when there is none or it is forged.

    The one place the shape rule lives. Four hand-kept copies of it drifted, and a `decision`
    whose state was 5, null, a list or "blocked" passed one check and failed the next: `status`
    recommended a move and the gate refused it.
    """
    decision = manifest.get("decision")
    return decision if _is_decision(decision) else None


def _history_is_sound(manifest: dict) -> bool:
    history = manifest.get("decisions", [])
    return isinstance(history, list) and all(isinstance(h, dict) for h in history)


def history(manifest: dict) -> list[dict]:
    """The decision history, or [] when it is not the shape the gate writes. For display."""
    return manifest.get("decisions") or [] if _history_is_sound(manifest) else []


def annotations(manifest: dict) -> list[dict]:
    """The annotations, keeping only entries of the shape the gate writes. For display."""
    notes = manifest.get("annotations")
    return [n for n in notes if isinstance(n, dict)] if isinstance(notes, list) else []


def _decision_shape_error(manifest: dict) -> str:
    """Why the recorded decision fields cannot be trusted, or "" when their shape is sound."""
    if manifest.get("decision") is not None and recorded_decision(manifest) is None:
        return "the recorded decision is malformed in the manifest"
    if not _history_is_sound(manifest):
        return "the decision history is malformed in the manifest"
    return ""


def _set_aside_malformed(manifest: dict) -> tuple[dict | None, bool]:
    """Move untrustworthy decision fields to their own keys, and return the trustworthy prior
    decision and whether anything moved. Nothing is erased; nothing malformed is acted on."""
    prior = recorded_decision(manifest)
    moved = False
    if manifest.get("decision") is not None and prior is None:
        manifest["decision_malformed"] = manifest["decision"]
        manifest["decision"] = None
        moved = True
    if not _history_is_sound(manifest):
        manifest["decisions_malformed"] = manifest.pop("decisions")
        moved = True
    if not isinstance(manifest.get("annotations", []), list):
        manifest["annotations_malformed"] = manifest.pop("annotations")
        moved = True
    return prior, moved


def _supersedes(prior: dict | None) -> dict | None:
    return {k: prior.get(k) for k in ("state", "by", "at")} if prior else None


def verify_artifacts(d: Path, manifest: dict) -> None:
    """Raise GateError unless the manifest agrees with the bytes on disk.

    Without this, approval attests to a JSON file that anyone can edit: flipping `review.ok` to
    true, or swapping an artifact between `show` and `approve`, would otherwise produce a clean
    approval with no trace. `approve` refuses on the error, `reject` records it as
    `verification_error`, and `status` reports it. The manifest is editable, so every field
    read from it is checked for shape before use: a wrong type that escaped as anything other
    than GateError left the run with no command the gate would accept.
    """
    shape = _decision_shape_error(manifest)
    if shape:
        raise GateError(shape)
    for a in manifest.get("artifacts", []):
        if a.get("error"):
            if a.get("file"):
                # The orchestrator records a failed seat with no file. Both at once is an edit,
                # and trusting `error` would skip every check below for bytes that exist.
                raise GateError(f"artifact for {a.get('role')!r} has both an error and a file")
            continue
        if not a.get("file"):
            # Every artifact is either a file on disk or a recorded error. Neither means the
            # manifest was edited: clearing `error` alone would otherwise skip verification.
            raise GateError(f"artifact for {a.get('role')!r} has neither a file nor an error")
        review = a.get("review")
        if not isinstance(a["file"], str) or (review is not None and not isinstance(review, dict)):
            raise GateError(f"artifact for {a.get('role')!r} is malformed in the manifest")
        if not isinstance(a.get("sha256"), str) or not a["sha256"]:
            # Every run records a digest. A missing one is an edit, and treating it as "nothing to
            # compare" let any bytes at all be approved.
            raise GateError(f"artifact {a['file']!r} has no recorded sha256")
        path = d / a["file"]
        try:
            # An absolute path, `..`, or a symlink would verify a file the run never wrote.
            inside = path.resolve().is_relative_to(d.resolve())
            present = inside and path.is_file()
            text = path.read_bytes().decode("utf-8") if present else ""
        except (OSError, ValueError, RuntimeError) as exc:
            # A binary file saved over a deliverable, an unreadable one, a name the filesystem
            # rejects (a null byte, too long) and a symlink loop (RuntimeError on 3.12) are all a
            # failed check. Letting any of them escape left `status` and `reject` both crashing.
            raise GateError(f"artifact {a['file']!r} cannot be read as text ({exc})") from exc
        if not inside:
            raise GateError(f"artifact {a['file']!r} is outside the run directory")
        if not present:
            raise GateError(f"artifact {a['file']!r} is missing")
        if sha256_text(text) != a["sha256"]:
            # Bytes first, because a deliverable containing a carriage return is hashed with it.
            # Then with line endings normalised, because Windows text-mode writes and git
            # autocrlf checkouts turn \n into \r\n after the digest was taken. A change of line
            # endings alone is not a change of content.
            normalised = text.replace("\r\n", "\n")
            if sha256_text(normalised) != a["sha256"]:
                raise GateError(f"artifact {a['file']!r} changed since the run")
            text = normalised
        recomputed = review_text(text)
        recorded = (review or {}).get("ok")
        if recomputed.ok != bool(recorded):
            raise GateError(
                f"manifest disagrees with {a['file']!r} (recorded ok={recorded}, "
                f"recomputed ok={recomputed.ok})"
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

    # A malformed decision already failed verification above; branch as if none were recorded.
    decision = recorded_decision(manifest) or {}
    if state in ("approved", "rejected"):
        action = "done"
    elif live:
        action = "wait"
    elif decision.get("state") in _DECISION_ACTION:
        # A decision is recorded but the move did not complete; re-running that same command
        # finishes it. The one exception mirrors `_decide`: a recorded approval that can no
        # longer be completed, because its bytes fail the check or its run is marked
        # interrupted, may only be superseded by a reject.
        action = _DECISION_ACTION[decision["state"]]
        if action == "approve" and (not verified or recorded in INTERRUPTED_STATUSES):
            action = "reject"
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
        if recorded_decision(m) and m.get("status") != state:
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
    try:
        verify_artifacts(src, manifest)
        unverified = ""
    except GateError as exc:
        # Approving attests to the bytes, so bytes that fail the check cannot be approved.
        # Rejecting attests to nothing. Refusing it too left a tampered run with no command the
        # gate would accept while `status` recommended `reject` — the exact contradiction
        # `pending_action` exists to prevent. The failure is recorded in the decision instead.
        if decision == "approved":
            raise GateError(f"{exc}; refusing to approve") from exc
        unverified = str(exc)
    flagged = flagged_roles(manifest.get("artifacts", []))
    if manifest.get("status") in INTERRUPTED_STATUSES and decision == "approved":
        raise GateError(f"run '{run_id}' was interrupted before it finished; reject it instead")
    # A malformed decision failed verification, so only a reject reaches here; it is set aside
    # under its own key and never trusted as a decision to complete.
    prior, moved = _set_aside_malformed(manifest)
    # A recorded approval that can no longer be completed, because its bytes fail the check or
    # its run is marked interrupted (which `approve` refuses above), may be superseded by a
    # reject. It stays in `decisions`; nothing recorded is erased.
    stale = bool(unverified) or manifest.get("status") in INTERRUPTED_STATUSES
    superseding = bool(prior) and prior["state"] == "approved" and stale
    if prior and not superseding:
        # A decision was recorded but the move did not complete. Only the same decision may
        # finish it (the supersede above is the one exception); a different one is refused so
        # nobody overwrites a recorded decision.
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
    if not prior or superseding:
        try:
            # Whoever creates this wins; the loser gets a clear error instead of both
            # "succeeding" and leaving the directory and the manifest disagreeing.
            claim = SUPERSEDE_CLAIM if superseding else DECISION_CLAIM
            os.close(os.open(src / claim, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
        except FileExistsError as exc:
            raise GateError(f"run '{run_id}' is being decided by another process") from exc
        try:
            _record_decision(
                src,
                manifest,
                decision=decision,
                by=by,
                note=note,
                forced=bool(force and flagged),
                flagged=flagged,
                unverified=unverified,
                superseded=prior if superseding else None,
            )
        except BaseException:
            # Nothing was recorded, so the claim must not outlive this attempt: a stale claim
            # refused every later decision, including the reject `status` recommends. A crash
            # hard enough to skip this still leaves the file; delete it by hand after checking
            # no decision is in progress.
            (src / claim).unlink(missing_ok=True)
            raise
    elif moved:
        # Completing a recorded decision writes nothing new, but a set-aside must still reach
        # disk, or the decided run keeps the malformed history that failed verification.
        write_manifest(src, manifest)
    dst.parent.mkdir(parents=True, exist_ok=True)
    # The dst.exists() check above is the real guard: os.rename onto an existing empty
    # directory succeeds silently on POSIX.
    os.rename(src, dst)
    decided = manifest["decision"]
    event = {
        "event": decision,
        "run_id": run_id,
        "by": decided.get("by"),
        "note": decided.get("note"),
        "forced": decided.get("forced"),
        "completed_by": by.strip() if prior and not superseding else None,
    }
    # The manifest is editable; the log is where an override has to be visible too.
    for key in ("supersedes", "verification_error"):
        if key in decided:
            event[key] = decided[key]
    append_log(event, log_file)
    log.info("run %s %s by %s", run_id, decision, decided.get("by"))
    return manifest


def _record_decision(
    src: Path,
    manifest: dict,
    *,
    decision: str,
    by: str,
    note: str,
    forced: bool,
    flagged: list[str],
    unverified: str,
    superseded: dict | None,
) -> None:
    """Append the decision to the history and write it in place, before the move."""
    entry = {
        "state": decision,
        "by": by.strip(),
        "note": note.strip(),
        "at": now_iso(),
        "forced": forced,
        "flagged_roles": flagged,
    }
    if unverified:
        entry["verification_error"] = unverified
    if superseded:
        entry["supersedes"] = _supersedes(superseded)
    # `decisions` is the append-only history, including anything later superseded by a reopen
    # or by a reject of an approval that can no longer be completed (see `supersedes`). `decision`
    # is whichever one is operative now, so existing readers and the rendered report keep
    # working.
    manifest.setdefault("decisions", []).append(entry)
    manifest["decision"] = entry
    manifest["status"] = decision
    # Record the decision in place first, then move: a crash between the two leaves a run in
    # pending/ whose manifest already carries the decision; re-running completes the move.
    write_manifest(src, manifest)


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
    # Kept, never erased; a non-list here crashed every annotation with AttributeError.
    _set_aside_malformed(manifest)
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
    # A decided run whose decision fields were edited offered reopen, and reopen then crashed
    # on them. Set aside like everywhere else; `supersedes` names only a trustworthy decision.
    superseded, _ = _set_aside_malformed(manifest)
    entry = {
        "state": "reopened",
        "by": by.strip(),
        "note": reason.strip(),
        "at": now_iso(),
        "supersedes": _supersedes(superseded),
    }
    manifest.setdefault("decisions", []).append(entry)
    manifest["decision"] = None  # nothing is operative until someone decides again
    manifest["status"] = "pending"
    write_manifest(src, manifest)
    dst.parent.mkdir(parents=True, exist_ok=True)
    os.rename(src, dst)
    # The old claim marker would otherwise block the next decision on this run.
    (dst / DECISION_CLAIM).unlink(missing_ok=True)
    (dst / SUPERSEDE_CLAIM).unlink(missing_ok=True)
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
