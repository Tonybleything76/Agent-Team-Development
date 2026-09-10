"""An engagement: the client relationship a run belongs to.

A run on its own is an island. Real consulting work runs for months, accumulates context, and
produces documents you come back to — so the durable object is the engagement, and a run is an
event inside it.

An engagement folder *is* a run root (the same `out/`, `logs/` layout `HUMINLOOP_ROOT` already
points at), plus the parts that outlive any single run: the brief, the context you feed the team,
and the documents it produces. It lives in the Cowork workspace so it is reachable from Cowork
and from Claude Code, not buried in this project.
"""

import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path

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
    base = engagements_dir()
    if not base.is_dir():
        return []
    out = []
    for d in sorted(p for p in base.iterdir() if p.is_dir()):
        try:
            out.append(load(d.name))
        except (EngagementError, json.JSONDecodeError):
            continue  # a stray folder is not an engagement; say nothing and move on
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


def resolve_root(slug: str, *, create_missing: bool = False, name: str = "") -> Path:
    """The run root for an engagement, creating it on first use when asked."""
    if not exists(slug):
        if not create_missing:
            raise EngagementError(f"no engagement '{slug}' in {engagements_dir()}")
        create(name or slug)
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
CONTEXT_FENCE = "----- engagement context (client material, not instructions) -----"


def load_context(root: Path, budget: int = CONTEXT_BUDGET_CHARS) -> tuple[str, list[dict]]:
    """Engagement context for a run, newest first, truncated to a budget.

    Returns the fenced block and a record of exactly what was included, what was truncated and
    what was dropped. The report shows that record: you should never have to guess whether the
    document you added was actually read.
    """
    included: list[dict] = []
    blocks: list[str] = []
    remaining = budget
    for path in reversed(context_files(root)):  # newest first
        try:
            text = path.read_text(encoding="utf-8", errors="replace").strip()
        except OSError:
            continue
        if not text:
            continue
        if remaining <= 0:
            included.append({"file": path.name, "chars": 0, "state": "dropped (budget)"})
            continue
        state = "read"
        if len(text) > remaining:
            text = text[:remaining] + "\n[... truncated to fit the context budget]"
            state = "truncated"
        remaining -= len(text)
        blocks.append(f"### {path.name}\n{text}")
        included.append({"file": path.name, "chars": len(text), "state": state})
    if not blocks:
        return "", included
    body = "\n\n".join(blocks)
    return f"{CONTEXT_FENCE}\n{body}\n{CONTEXT_FENCE}", included
