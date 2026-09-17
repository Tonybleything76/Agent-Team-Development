"""An engagement: the client relationship a run belongs to.

A run on its own is an island. Real consulting work runs for months, accumulates context, and
produces documents you come back to — so the durable object is the engagement, and a run is an
event inside it.

An engagement folder *is* a run root (the same `out/`, `logs/` layout `HUMINLOOP_ROOT` already
points at), plus the parts that outlive any single run: the brief, the context you feed the team,
and the documents it produces. It lives in the Cowork workspace so it is reachable from Cowork
and from Claude Code, not buried in this project.
"""

import difflib
import hashlib
import json
import os
import re
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path

from .governance import ENGAGEMENT_FENCE, fenced, one_line

ENGAGEMENTS_ENV = "HUMINLOOP_ENGAGEMENTS"
DEFAULT_ENGAGEMENTS_DIR = Path.home() / "Cowork" / "Engagements"
MANIFEST = "engagement.json"
CONTEXT_DIR = "context"
DOCUMENTS_DIR = "documents"


class EngagementError(Exception):
    pass


def engagements_dir() -> Path:
    return Path(os.getenv(ENGAGEMENTS_ENV) or DEFAULT_ENGAGEMENTS_DIR)


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", (name or "").lower()).strip("-")
    if not slug:
        raise EngagementError(f"cannot make a folder name from {name!r}")
    return slug


def path_for(slug: str) -> Path:
    # The slug becomes a directory name, so it may never climb out of the engagements directory.
    if slug != slugify(slug):
        raise EngagementError(f"invalid engagement slug {slug!r}")
    return engagements_dir() / slug


def exists(slug: str) -> bool:
    return (path_for(slug) / MANIFEST).is_file()


def load(slug: str) -> dict:
    p = path_for(slug) / MANIFEST
    if not p.is_file():
        raise EngagementError(f"no engagement '{slug}' in {engagements_dir()}")
    return json.loads(p.read_text(encoding="utf-8"))


def list_all() -> list[dict]:
    """Every engagement, including the ones whose manifest has gone bad.

    Two different things used to be swallowed by one `continue`. A folder with no manifest is
    a stray directory and rightly says nothing. A folder whose manifest exists and will not
    parse is a real engagement, with a client's runs and context inside it, and hiding it means
    the list reports "no engagements" for a directory that plainly has one — the same failure
    `gate.list_runs` already refuses to have for runs.
    """
    base = engagements_dir()
    if not base.is_dir():
        return []
    out = []
    for d in sorted(p for p in base.iterdir() if p.is_dir()):
        if not (d / MANIFEST).is_file():
            continue  # a stray folder is not an engagement; say nothing and move on
        try:
            out.append(load(d.name))
        except (EngagementError, json.JSONDecodeError, OSError) as exc:
            out.append(
                {
                    "slug": d.name,
                    "name": "",
                    "created_at": "",
                    "status": "corrupt",
                    "error": f"unreadable {MANIFEST}: {exc}",
                }
            )
    return out


def create(name: str, brief: str = "", client: str = "") -> Path:
    slug = slugify(name)
    root = path_for(slug)
    if (root / MANIFEST).is_file():
        raise EngagementError(f"engagement '{slug}' already exists at {root}")
    for sub in (CONTEXT_DIR, DOCUMENTS_DIR, "out", "logs"):
        (root / sub).mkdir(parents=True, exist_ok=True)
    manifest = {
        "slug": slug,
        "name": name,
        "client": client or name,
        "brief": brief,
        "created_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "status": "active",
    }
    (root / MANIFEST).write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    (root / CONTEXT_DIR / "README.md").write_text(_CONTEXT_README, encoding="utf-8")
    (root / "CLAUDE.md").write_text(_claude_md(manifest), encoding="utf-8")
    return root


def _no_such_engagement(slug: str) -> str:
    """Say which engagement was meant, not just that this one is missing.

    A transposed letter used to create a whole second engagement folder and run the work into
    it; `pending` then reported "no pending runs" and the run was simply gone from view. The
    near-miss is the entire difference between a typo you fix in five seconds and a silent
    fork of a client's record.
    """
    known = [e["slug"] for e in list_all()]
    msg = f"no engagement '{slug}' in {engagements_dir()}"
    near = difflib.get_close_matches(slug, known, n=3, cutoff=0.6)
    if near:
        return msg + "; did you mean " + " or ".join(repr(s) for s in near) + "?"
    if known:
        return msg + "; known engagements: " + ", ".join(known)
    return msg + '; create one first with: huminloop engagement new "<name>"'


def resolve_root(slug: str) -> Path:
    """The run root for an existing engagement.

    Never creates one. `engagement new` is the only way an engagement comes into being, so a
    mistyped `--engagement` is an error a human sees rather than a phantom folder the work
    quietly disappears into.
    """
    if not exists(slug):
        raise EngagementError(_no_such_engagement(slug))
    return path_for(slug)


def context_files(root: Path) -> list[Path]:
    """What the team should read before drafting. Newest last, README excluded."""
    d = root / CONTEXT_DIR
    if not d.is_dir():
        return []
    files = [
        p
        for p in d.rglob("*")
        if p.is_file() and p.suffix.lower() in (".md", ".txt") and p.name != "README.md"
    ]
    return sorted(files, key=lambda p: (p.stat().st_mtime, p.name))


_CONTEXT_README = """# Context

Anything you drop in here is read by the team before it drafts: discovery notes, meeting
transcripts, the client's current architecture, an org chart, a previous deliverable.

Plain text and markdown (`.md`, `.txt`). One topic per file, named so you can tell them apart
in a list — `2026-09-10-discovery-notes.md` beats `notes2.md`.

Every run's report states which of these the team actually read, so you never have to guess
whether the thing you added made it in.
"""


def _claude_md(m: dict) -> str:
    return f"""# {m["name"]} — engagement

Client engagement run through HuminLoop Agents. This folder is the durable record; individual
runs are events inside it.

- **Brief:** {m["brief"] or "(none recorded yet)"}
- **Started:** {m["created_at"][:10]}
- **Slug:** `{m["slug"]}`

## Layout

- `context/` — what you feed the team. Everything here is read before each run drafts.
- `out/pending|approved|rejected/` — runs, each with its artifacts and manifest.
- `documents/` — deliverable drafts produced for this engagement.
- `logs/runs.jsonl` — append-only record of every run and every human decision.

## Working here

From this repo: `huminloop --engagement {m["slug"]} run "<task>"`, then `pending`, `show`,
`approve` / `reject` / `annotate` / `reopen`, or `serve` for the browser inbox.

Nothing leaves `pending/` without a named human decision. Approving a run the team escalated
questions on requires an explicit override with a written reason, and that override is recorded
permanently.
"""


# What the team can be shown before it drafts. Beyond this the oldest files are dropped, and
# the run records which ones made it in, so a silent omission is impossible.
CONTEXT_BUDGET_CHARS = 24000
CONTEXT_FENCE = ENGAGEMENT_FENCE  # one definition, in governance, so fenced() knows them all
TRUNCATION_NOTE = "\n[... truncated to fit the context budget]"


# How far past the budget we will read looking for real content behind a wall of whitespace
# before giving up and calling the file truncated. Bounds a pathological all-blank file.
WHITESPACE_PROBE_CHARS = 8192
WHITESPACE_PROBE_LIMIT = 1_000_000


def _overflows(handle, chunk: str, remaining: int) -> bool:
    """Does real content fall outside the budget, or is the overflow only whitespace?

    `len(chunk) > remaining` alone called a ten-character document "truncated" because it had
    five thousand trailing blank lines: a false entry in the audit record, a false truncation
    note handed to the model, and budget charged for text nobody sent.
    """
    if len(chunk) <= remaining:
        return False
    if len(chunk.rstrip()) > remaining:
        return True  # visible content already exceeds what is left
    probed = 0
    while probed < WHITESPACE_PROBE_LIMIT:
        more = handle.read(WHITESPACE_PROBE_CHARS)
        if not more:
            return False  # the entire tail was whitespace; the document itself fitted
        if more.strip():
            return True  # real content beyond the budget
        probed += len(more)
    return True  # gave up looking; say truncated rather than claim it all fitted


def _contained(path: Path, base: Path) -> str:
    """ "" when `path`, symlinks followed, is really inside `base`; else why it is refused.

    A `.md` symlink dropped in `context/` is an ordinary file to `rglob` and `is_file`, so
    without this the team reads and the provider receives a document from anywhere on the
    filesystem — another client's contract, `~/.ssh/config` — while the audit record shows only
    the innocent local basename. The boundary is the engagement, not `context/` itself, so
    pointing at a sibling `documents/` file still works.

    The two failures are told apart deliberately. A file that resolves outside is a refusal; a
    file that will not resolve at all has usually just been deleted between `context_files()`
    listing it and this call. Reporting the second as the first puts a wrong answer in an audit
    record, which is worse than reporting nothing.
    """
    try:
        real = path.resolve(strict=True)
    except OSError as exc:
        return f"unresolvable ({exc.strerror or exc})"
    return "" if real.is_relative_to(base) else "refused (resolves outside the engagement)"


def load_context(root: Path, budget: int = CONTEXT_BUDGET_CHARS) -> tuple[str, list[dict]]:
    """Engagement context for a run, newest first, truncated to a budget.

    Returns the fenced block and a record of exactly what was included, what was truncated and
    what was dropped. The report shows that record: you should never have to guess whether the
    document you added was actually read.

    Every candidate file earns a row, including the ones that contributed nothing — refused,
    unreadable, empty, dropped. A file that simply disappears from this list is the silent
    omission this whole system exists to prevent, and it is worse here than anywhere else: the
    absence looks exactly like "you never added it".
    """
    included: list[dict] = []
    blocks: list[str] = []
    remaining = budget
    base = Path(os.path.realpath(root))
    for path in reversed(context_files(root)):  # newest first
        refusal = _contained(path, base)
        if refusal:
            row = {"file": path.name, "chars": 0, "state": refusal}
            if refusal.startswith("refused"):
                # The basename is what a reviewer sees; where it actually points is the only
                # part that tells them what nearly went out. A file that vanished has no
                # target worth recording.
                row["resolves_to"] = os.path.realpath(path)
            included.append(row)
            continue
        if remaining <= 0:
            included.append({"file": path.name, "chars": 0, "state": "dropped (budget)"})
            continue
        try:
            with path.open("r", encoding="utf-8", errors="replace") as f:
                # At most what can still fit, plus one character to tell "exactly fits" from
                # "overflows". read_text() pulled the whole file into memory first: a
                # multi-gigabyte transcript dropped in context/ was read end to end only to
                # discover that twenty characters of it fit the budget.
                chunk = f.read(remaining + 1)
                # Inside the `with`: the probe may need to keep reading this same handle.
                over_budget = _overflows(f, chunk, remaining)
        except OSError as exc:
            included.append(
                {"file": path.name, "chars": 0, "state": f"unreadable ({exc.strerror or exc})"}
            )
            continue
        text = chunk.strip()
        if not text:
            # `_overflows` already knows whether real content lies past what we read, and the
            # first version of this branch threw that answer away: a client file that merely
            # opened with blank lines was recorded as empty, and its content never reached the
            # team. Blank is blank only when nothing follows it.
            included.append(
                {
                    "file": path.name,
                    "chars": 0,
                    "state": "dropped (budget)" if over_budget else "empty",
                }
            )
            continue
        state = "read"
        if over_budget or len(text) > remaining:
            text = text[:remaining]
            state = "truncated"
        # What actually went out, before the note is appended: `chars` answers "how much of my
        # document did the team see", and counting our own footer into that overstates it.
        sent = len(text)
        if state == "truncated":
            text += TRUNCATION_NOTE
        remaining -= len(text)
        blocks.append(f"### {path.name}\n{text}")
        included.append({"file": path.name, "chars": sent, "state": state})
    if not blocks:
        return "", included
    body = "\n\n".join(blocks)
    return fenced(body, CONTEXT_FENCE), included


# States that mean bytes from this file actually reached the fenced block. Everything else in
# `context_read` is a row explaining why a file contributed nothing.
SENT_STATES = ("read", "truncated")
# Where a run keeps its own copy of the material it was given. A resynthesize an hour later must
# integrate the client material the specialists actually saw, not whatever `context/` holds by
# then — the folder is a live directory a human edits between runs.
RUN_CONTEXT_DIR = "context"
RUN_CONTEXT_FILE = "context.md"


@dataclass(frozen=True)
class LoadedContext:
    """One run's client material: what will be sent, the record of how it was assembled, and
    the human clearance that permits sending it.

    Assembled once and carried, never re-read. Reading a second time between showing a human
    what they are clearing and handing it to the provider would mean the bytes they approved
    and the bytes that went out are only probably the same.
    """

    block: str
    read: list[dict]
    source_dir: str
    clearance: dict | None = None

    @property
    def sent_files(self) -> list[str]:
        return [r["file"] for r in self.read if r["state"] in SENT_STATES]

    @property
    def chars(self) -> int:
        return len(self.block)

    @property
    def is_cleared(self) -> bool:
        """The clearance actually covers *these* bytes, not merely that some dict is present.

        `run()` used to test `not context.clearance`, so any truthy dict passed and the manifest
        then recorded it as the proof of who cleared what. The resynthesize door already
        verified the hash; this is the same proof, so the first and paid pass is not the weaker
        of the two.
        """
        c = self.clearance
        return bool(
            isinstance(c, dict)
            and c.get("sha256") == hashlib.sha256(self.block.encode("utf-8")).hexdigest()
            and list(c.get("files") or []) == self.sent_files
        )

    def cleared_by(self, by: str, method: str) -> "LoadedContext":
        """A copy carrying the record of who cleared exactly these bytes, and how.

        The approved design doc said neither confidentiality answer would be written into
        `manifest.json`, on the reasoning that a pre-condition is not a fact about the run.
        That is superseded deliberately (eng review T5, 2026-09-17): every other human decision
        in this system is recorded permanently so it can be proven later, real client
        engagements began after that doc was written, and "was this cleared, by whom, over
        which bytes" is exactly the question a client asks afterward. A boolean nobody wrote
        down cannot answer it.
        """
        return replace(
            self,
            clearance={
                "by": by,
                "at": datetime.now(UTC).isoformat(timespec="seconds"),
                "source_dir": self.source_dir,
                "files": self.sent_files,
                "bytes": len(self.block.encode("utf-8")),
                # Over the assembled block, so the record pins the exact material sent rather
                # than a directory whose contents move.
                "sha256": hashlib.sha256(self.block.encode("utf-8")).hexdigest(),
                "method": method,
            },
        )


def prepare_context(root: Path, budget: int = CONTEXT_BUDGET_CHARS) -> LoadedContext:
    """Everything a run needs to know about its engagement context, read exactly once."""
    block, read = load_context(root, budget)
    # Absolute on purpose. base_root() defaults to Path("."), so a run outside an
    # engagement still reads ./context/ — legitimate, but only if the prompt says plainly
    # which directory on disk it means rather than printing a bare "context".
    return LoadedContext(
        block=block, read=read, source_dir=str((Path(root) / CONTEXT_DIR).resolve())
    )


def snapshot_context(run_out: Path, block: str) -> None:
    """Keep the run's own copy of the material it was given, inside the run directory.

    Lives in a subdirectory so it never lands in the `*.md` glob that `show` and the dashboard's
    Documents tab use to list artifacts: this is evidence, not something the team produced.
    """
    if not block:
        return
    d = run_out / RUN_CONTEXT_DIR
    d.mkdir(parents=True, exist_ok=True)
    (d / RUN_CONTEXT_FILE).write_text(block, encoding="utf-8")


def read_snapshot(run_out: Path) -> str:
    """The raw context this run was given, or "" when it was given none.

    Raw on purpose: nothing here proves the bytes are the ones a human cleared. Anything about
    to hand this to a provider must go through `cleared_snapshot` instead.
    """
    p = run_out / RUN_CONTEXT_DIR / RUN_CONTEXT_FILE
    try:
        return p.read_text(encoding="utf-8")
    except OSError:
        return ""


def cleared_snapshot(
    run_out: Path, clearance: dict | None, context_read: list[dict] | None = None
) -> str:
    """The run's context, proven to be exactly the bytes a named human cleared.

    `run()` refuses to send uncleared client material, but it was the only door with a lock on
    it: `resynthesize()` read this snapshot straight off disk and handed it to the provider,
    so (a) material edited after clearance went out under the original approver's name, and
    (b) a run that never had any context at all would happily send a `context.md` dropped into
    its directory afterwards, with `context_clearance: None` still in the manifest. Both
    reproduced, 2026-09-17.

    The snapshot sits outside `gate.verify_artifacts` — it is evidence the team was given, not
    an artifact the team produced — so the clearance record's own sha256 is what pins it.
    """
    if clearance is not None and not isinstance(clearance, dict):
        # Straight off a manifest, so it can be any JSON. Fail with the error the CLI prints
        # cleanly rather than an AttributeError traceback from .get().
        raise EngagementError(
            f"{run_out.name} has a context_clearance that is not an object; manifest is corrupt"
        )
    block = read_snapshot(run_out)
    # The run's own record of what it was given. Keying the guard on `clearance` alone left the
    # original hole open through the null-clearance branch: with context_clearance absent and
    # the snapshot removed, this returned "" and the lead was rewritten having been given
    # nothing, while context_read still advertised the files as read.
    sent = [r for r in (context_read or []) if r.get("state") in SENT_STATES]
    if not block:
        if clearance or sent:
            # Failing open here would be the silent omission this function exists to stop: the
            # manifest still asserts a named human cleared N files, and the lead would quietly
            # rewrite the client-facing recommendation having been given nothing.
            by = one_line(str((clearance or {}).get("by") or "nobody"))
            count = len(sent) or len((clearance or {}).get("files") or [])
            raise EngagementError(
                f"{run_out.name} says it was given {count} context file(s) (cleared by {by}), "
                "but its snapshot is missing or empty; refusing to resynthesize without the "
                "material it says it had"
            )
        return ""
    if not clearance:
        raise EngagementError(
            f"{run_out.name} carries engagement context that nobody cleared; refusing to send it"
        )
    digest = hashlib.sha256(block.encode("utf-8")).hexdigest()
    if digest != clearance.get("sha256"):
        raise EngagementError(
            f"{run_out.name}'s context has changed since "
            f"{one_line(str(clearance.get('by') or 'it was'))} cleared it; re-run rather than "
            "sending material nobody approved"
        )
    return block
