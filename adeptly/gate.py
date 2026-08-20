"""Human approval gate.

Nothing an agent produces is 'released' until a named person moves it out of pending/.
The gate is deliberately dumb: it reads and writes files and a log, and that is all.
"""

import logging
import shutil
from datetime import UTC, datetime
from pathlib import Path

from .storage import append_log, artifact_root, find_run, read_manifest, run_dir, write_manifest

log = logging.getLogger(__name__)


class GateError(Exception):
    pass


def list_runs(state: str = "pending", root: Path | None = None) -> list[dict]:
    root = artifact_root(root)
    base = root / state
    if not base.exists():
        return []
    out = []
    for d in sorted(p for p in base.iterdir() if (p / "manifest.json").exists()):
        out.append(read_manifest(d))
    return out


def _decide(run_id: str, decision: str, by: str, note: str, root: Path | None, log_file) -> dict:
    if not by or not by.strip():
        raise GateError("a named approver is required (--by)")
    root = artifact_root(root)
    found = find_run(root, run_id)
    if not found:
        raise GateError(f"run '{run_id}' not found under {root}")
    state, src = found
    if state != "pending":
        raise GateError(f"run '{run_id}' is already {state}")
    manifest = read_manifest(src)
    manifest["decision"] = {
        "state": decision,
        "by": by.strip(),
        "note": note,
        "at": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    manifest["status"] = decision
    dst = run_dir(root, decision, run_id)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst))
    write_manifest(dst, manifest)
    append_log({"event": decision, "run_id": run_id, "by": by, "note": note}, log_file)
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
    found = find_run(artifact_root(root), run_id)
    if found and found[0] == "pending":
        flagged = [
            a["role"]
            for a in read_manifest(found[1])["artifacts"]
            if a.get("review", {}).get("verdict") != "APPROVE"
        ]
        if flagged and not force:
            raise GateError(
                f"governance flagged {flagged}; re-run, or approve with --force and a note"
            )
        if flagged and not note.strip():
            raise GateError("--force requires a --note explaining why")
    return _decide(run_id, "approved", by, note, root, log_file)


def reject(run_id: str, by: str, reason: str, *, root: Path | None = None, log_file=None) -> dict:
    if not reason or not reason.strip():
        raise GateError("a reason is required to reject")
    return _decide(run_id, "rejected", by, reason, root, log_file)
