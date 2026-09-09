import argparse
import json
import logging
import os
import sys
from pathlib import Path

from . import __version__, gate, orchestrator, stats
from .governance import strip_controls
from .llm import PROVIDERS, get_llm
from .render import RenderError, render_run
from .roles import ROLES
from .storage import (
    ARTIFACT_DIR_ENV,
    DEFAULT_ARTIFACT_DIR,
    DEFAULT_LOG_DIR,
    LOG_DIR_ENV,
    ROOT_ENV,
    STATES,
    StorageError,
    artifact_root,
    find_run,
    log_path,
    read_manifest,
)

log = logging.getLogger(__name__)


# A .env may only set variables this application owns. Without an allowlist, a .env sitting in
# any directory you run `huminloop` from could set OPENAI_BASE_URL or HTTPS_PROXY and silently
# redirect model calls (with the Authorization header) to another host.
DOTENV_ALLOWED = frozenset(
    {
        "LLM_PROVIDER",
        "LLM_MAX_TOKENS",
        "LLM_TIMEOUT_S",
        "OPENROUTER_API_KEY",
        "OPENROUTER_MODEL",
        "OPENAI_API_KEY",
        "OPENAI_MODEL",
        "ANTHROPIC_API_KEY",
        "ANTHROPIC_MODEL",
        ROOT_ENV,
        ARTIFACT_DIR_ENV,
        LOG_DIR_ENV,
    }
)


def _dotenv_allows(key: str) -> bool:
    return key in DOTENV_ALLOWED or key.startswith(("OPENROUTER_MODEL_", "OPENROUTER_EFFORT"))


def load_dotenv(path: Path) -> None:
    """Minimal .env loader: KEY=value lines, '#' comments; never overrides the real environment.

    Only keys this application owns are set; anything else in the file is ignored with a warning.
    """
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key.startswith("export "):
            key = key[len("export ") :].strip()
        value = value.strip()
        if value[:1] in ("'", '"'):
            quote = value[0]
            end = value.find(quote, 1)
            value = value[1:end] if end > 0 else value[1:]
        else:
            value = value.split(" #", 1)[0].split("\t#", 1)[0].strip()
        if not key or key in os.environ:
            continue
        if not _dotenv_allows(key):
            log.warning("ignoring unsupported key %r in %s", key, path)
            continue
        os.environ[key] = value


def _cmd_run(args) -> int:
    llm = get_llm(args.provider)
    rec = orchestrator.run(args.task, llm=llm, critique=args.critique)
    print(f"run_id: {rec.run_id}  provider: {rec.provider}")
    print(f"plan:   {rec.plan['roles']}  (rules: {rec.plan['matched_rules'] or 'default'})")
    for a in rec.artifacts:
        if a.role == "engagement_lead" and not a.error:
            continue  # printed on its own line below, with its register counts
        if a.error:
            print(f"  {a.role:<18} ERROR   {a.error}")
        else:
            notes = list(a.review["issues"]) + list(a.process_flags)
            if a.critique:
                pts = a.critique["points"]
                kept = sum(1 for p in pts if p["disposition"] == "accepted")
                notes.insert(0, f"critique: {len(pts)} point(s), {kept} accepted")
            flag = "" if not a.process_flags else "*"
            print(f"  {a.role:<18} {a.review['verdict'] + flag:<9} {a.file}  {'; '.join(notes)}")
    if rec.synthesis:
        n = rec.synthesis
        print(
            f"  {'engagement lead':<18} synthesis  {n['decisions']} decision(s) open"
            f"  {n['disagreements']} disagreement(s)  {n['escalations']} escalated to you"
        )
    print(f"status: pending -> review with `huminloop show {rec.run_id}`, then approve or reject.")
    if rec.artifacts and all(a.error for a in rec.artifacts):
        # A run where nothing succeeded is a failure for anything scripting this command,
        # even though the run is still on disk for a human to reject.
        print("error: every specialist failed; see logs/runs.jsonl", file=sys.stderr)
        return 1
    return 0


def _cmd_resynthesize(args) -> int:
    llm = get_llm(args.provider)
    rec = orchestrator.resynthesize(args.run_id, llm=llm)
    lead = next((a for a in rec.artifacts if a.role == "engagement_lead"), None)
    if lead and lead.error:
        print(f"  engagement_lead    ERROR   {lead.error}", file=sys.stderr)
        print(f"status: resynthesis failed; run '{rec.run_id}' is still pending.", file=sys.stderr)
        return 1
    if rec.synthesis:
        n = rec.synthesis
        print(
            f"  {'engagement lead':<18} synthesis  {n['decisions']} decision(s) open"
            f"  {n['disagreements']} disagreement(s)  {n['escalations']} escalated to you"
        )
    print(f"status: pending -> review with `huminloop show {rec.run_id}`, then approve or reject.")
    return 0


def _cmd_roles(args) -> int:
    for r in ROLES.values():
        print(f"{r.key:<18} {r.tier.value:<14} {r.title}")
    return 0


def _cmd_pending(args) -> int:
    runs = gate.list_runs(args.state)
    if not runs:
        print(f"no {args.state} runs")
        return 0
    for m in runs:
        verdicts = [(a.get("review") or {}).get("verdict", "ERROR") for a in m.get("artifacts", [])]
        status = str(m.get("status") or "")
        flag = "" if status == args.state else f"  [{status}]"
        task = str(m.get("task") or "")[:50]
        created = str(m.get("created_at") or "")
        notes = len(m.get("annotations") or [])
        # A reopened run looks identical to a fresh one in the directory, so say so here.
        reopens = sum(1 for d in (m.get("decisions") or []) if d.get("state") == "reopened")
        marks = ""
        if notes:
            marks += f"  {notes} note(s)"
        if reopens:
            marks += f"  reopened x{reopens}"
        print(f"{m.get('run_id', '?')}  {created:<25} {task!r} {verdicts}{flag}{marks}")
    return 0


def _cmd_render(args) -> int:
    found = find_run(artifact_root(None), args.run_id)
    if not found:
        print(f"run {args.run_id} not found", file=sys.stderr)
        return 1
    _, d = found
    manifest = read_manifest(d)
    page = render_run(manifest, d)
    out = Path(args.out) if args.out else d / "run.html"
    out.write_text(page, encoding="utf-8")
    print(f"wrote {out}")
    return 0


def _cmd_show(args) -> int:
    found = find_run(artifact_root(None), args.run_id)
    if not found:
        print(f"run {args.run_id} not found", file=sys.stderr)
        return 1
    state, d = found
    manifest = read_manifest(d)
    print(json.dumps(manifest, indent=2))
    # Human commentary leads, because it is the part a reviewer most needs before deciding
    # and the part most easily lost in a long manifest.
    for entry in manifest.get("decisions") or []:
        if entry.get("state") == "reopened":
            was = entry.get("supersedes") or {}
            print(f"\n[reopened] by {entry['by']} at {entry['at']}: {entry['note']}")
            print(f"           supersedes {was.get('state')} by {was.get('by')} at {was.get('at')}")
    for note in manifest.get("annotations") or []:
        print(f"\n[note] {note['by']} at {note['at']} (run was {note['state_when_written']}):")
        print(f"       {strip_controls(note['note'])}")
    for f in sorted(d.glob("*.md")):
        body = strip_controls(f.read_text(encoding="utf-8"))
        print(f"\n===== {state}/{f.name} =====\n{body}")
    return 0


def _cmd_approve(args) -> int:
    m = gate.approve(args.run_id, args.by, args.note or "", force=args.force)
    print(f"approved {m['run_id']} by {m['decision']['by']}")
    return 0


def _cmd_reject(args) -> int:
    m = gate.reject(args.run_id, args.by, args.reason)
    print(f"rejected {m['run_id']} by {m['decision']['by']}")
    return 0


def _cmd_annotate(args) -> int:
    m = gate.annotate(args.run_id, args.by, args.note)
    print(f"annotated {m['run_id']} ({len(m['annotations'])} note(s)); status unchanged")
    return 0


def _cmd_reopen(args) -> int:
    m = gate.reopen(args.run_id, args.by, args.reason)
    prior = m["decisions"][-1].get("supersedes") or {}
    was = f"{prior.get('state')} by {prior.get('by')}" if prior else "a prior decision"
    print(f"reopened {m['run_id']} (superseded {was}); it is pending again")
    return 0


def _cmd_stats(args) -> int:
    events = stats.read_events(log_path(None))
    if not events:
        print("no run log yet")
        return 0
    summary = stats.summarize(events)
    for key, value in summary.items():
        if isinstance(value, float):
            print(f"  {key:<32} {value:.2f}")
        elif value is None:
            print(f"  {key:<32} n/a")
        else:
            print(f"  {key:<32} {value}")
    notes = stats.warnings(summary)
    if notes:
        print("\nworth a look:")
        for note in notes:
            print(f"  - {note}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="huminloop", description="Hierarchical agent team with a human approval gate"
    )
    p.add_argument("--version", action="version", version=f"huminloop {__version__}")
    p.add_argument("-v", "--verbose", action="store_true")
    p.add_argument(
        "--root",
        help="directory holding out/ and logs/; overrides ARTIFACT_DIR/LOG_DIR "
        "(default: $HUMINLOOP_ROOT or current directory)",
    )
    p.add_argument(
        "--env-file",
        default=os.getenv("HUMINLOOP_ENV_FILE", ".env"),
        help="dotenv file to load (default: $HUMINLOOP_ENV_FILE or .env)",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("run", help="route a task to specialists and park output in pending/")
    s.add_argument("task")
    s.add_argument("--provider", choices=PROVIDERS)
    s.add_argument(
        "--no-critique",
        dest="critique",
        action="store_false",
        help="skip the critique round (faster and cheaper; the draft is what you get)",
    )
    s.set_defaults(fn=_cmd_run)

    s = sub.add_parser(
        "resynthesize",
        help="retry the Engagement Lead against a pending run's existing artifacts",
    )
    s.add_argument("run_id")
    s.add_argument("--provider", choices=PROVIDERS)
    s.set_defaults(fn=_cmd_resynthesize)

    sub.add_parser("roles", help="list the team").set_defaults(fn=_cmd_roles)

    s = sub.add_parser("pending", help="list runs awaiting a human decision")
    s.add_argument("--state", default="pending", choices=STATES)
    s.set_defaults(fn=_cmd_pending)

    s = sub.add_parser("show", help="print a run's manifest and artifacts")
    s.add_argument("run_id")
    s.set_defaults(fn=_cmd_show)

    s = sub.add_parser(
        "render",
        help="render an approved or pending run to a self-contained HTML report",
    )
    s.add_argument("run_id")
    s.add_argument("--out", help="output path (default: <run_dir>/run.html)")
    s.set_defaults(fn=_cmd_render)

    s = sub.add_parser("approve", help="human approval: move a run to approved/")
    s.add_argument("run_id")
    s.add_argument("--by", required=True, help="name of the person approving")
    s.add_argument("--note")
    s.add_argument("--force", action="store_true", help="approve despite governance issues")
    s.set_defaults(fn=_cmd_approve)

    s = sub.add_parser("reject", help="human rejection: move a run to rejected/")
    s.add_argument("run_id")
    s.add_argument("--by", required=True)
    s.add_argument("--reason", required=True)
    s.set_defaults(fn=_cmd_reject)

    s = sub.add_parser("annotate", help="record a note on a run without deciding it")
    s.add_argument("run_id")
    s.add_argument("--by", required=True, help="name of the person writing the note")
    s.add_argument("--note", required=True)
    s.set_defaults(fn=_cmd_annotate)

    s = sub.add_parser(
        "reopen", help="take a decided run back to pending, superseding the decision"
    )
    s.add_argument("run_id")
    s.add_argument("--by", required=True)
    s.add_argument("--reason", required=True)
    s.set_defaults(fn=_cmd_reopen)

    sub.add_parser(
        "stats", help="what the run log says about how the team is working"
    ).set_defaults(fn=_cmd_stats)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )
    try:
        load_dotenv(Path(args.env_file))
        if args.root:
            # --root wins over anything .env says, including absolute ARTIFACT_DIR/LOG_DIR.
            os.environ[ROOT_ENV] = args.root
            os.environ[ARTIFACT_DIR_ENV] = DEFAULT_ARTIFACT_DIR
            os.environ[LOG_DIR_ENV] = DEFAULT_LOG_DIR
        return args.fn(args)
    except (gate.GateError, RenderError, StorageError, ValueError, RuntimeError, OSError) as exc:
        if args.verbose:
            raise
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
