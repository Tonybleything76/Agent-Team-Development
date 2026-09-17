import argparse
import getpass
import json
import logging
import os
import sys
from pathlib import Path

from . import __version__, engagement, gate, orchestrator, stats
from .dashboard import render_dashboard
from .governance import LINE_MAX_CHARS, one_line, strip_controls
from .llm import PROVIDERS, get_llm
from .render import RenderError, render_run
from .roles import ROLES
from .router import Router
from .storage import (
    ARTIFACT_DIR_ENV,
    DEFAULT_ARTIFACT_DIR,
    DEFAULT_LOG_DIR,
    LOG_DIR_ENV,
    ROOT_ENV,
    STATES,
    StorageError,
    artifact_root,
    base_root,
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


# Every seat that reasons about the work now carries the context (see llm.build_prompt and
# its siblings): the draft, the critic's read of it, and the author's revision, for each
# specialist and again for the Engagement Lead. An upper bound, because the revision only
# happens when the critic actually returned points.
_CALLS_PER_ROLE_WITH_CRITIQUE = 3


def _context_spend(task: str, critique: bool) -> tuple[list[str], int]:
    """Which roles this task routes to, and how many calls would carry the context.

    The router is keyword-based and deterministic, so asking it costs nothing and gives the
    real plan rather than an estimate — the same free dry-run the approved design doc puts
    before any spend confirmation.
    """
    roles = Router().route(task).roles
    per_role = _CALLS_PER_ROLE_WITH_CRITIQUE if critique else 1
    return roles, (len(roles) + 1) * per_role  # +1: the Engagement Lead


def _context_summary(ctx: engagement.LoadedContext, roles: list[str], calls: int) -> str:
    """What a human needs in front of them to answer "may this be sent" honestly.

    Not just which files: how big, from which directory on disk, to how many seats, over how
    many paid calls. "Yes" to one call and "yes" to thirty are different answers, and the
    person giving it should not have to work out which one they are giving.
    """
    lines = [
        f"This run would send {len(ctx.sent_files)} file(s) ({ctx.chars:,} characters) "
        f"from {one_line(ctx.source_dir)}",
        f"to {len(roles) + 1} seat(s) ({', '.join(roles)}, engagement_lead), "
        f"over up to {calls} provider call(s).",
        "",
    ]
    for r in ctx.read:
        # Both the filename and a symlink's target come off the filesystem and can carry ANSI
        # escapes. This is the exact text a human reads before answering y/N, so a crafted
        # name could scroll rows of it out of view. `_cmd_show` already sanitises model output
        # for the same reason; the consent prompt is a worse place to omit it.
        # one_line, not strip_controls: the latter keeps newlines by design, so a filename
        # containing one forged extra rows in this very list. Reproduced 2026-09-17.
        detail = f" -> {one_line(r['resolves_to'])}" if r.get("resolves_to") else ""
        # The filename shares a row with the state column, so it is bounded; the source
        # directory above stands alone and is never cut.
        name = one_line(r["file"], LINE_MAX_CHARS)
        lines.append(f"  {name:<40} {one_line(r['state'])}{detail}")
    return "\n".join(lines)


def _clear_context(args, ctx: engagement.LoadedContext) -> engagement.LoadedContext:
    """Answer "may this client material go to the provider" before the first call is made.

    The approved design doc names this as a hard constraint and nothing in the shipped code
    asked. It is asked here, where a human is, and recorded on the run (see
    LoadedContext.cleared_by). Clearing a run for the provider clears nothing else: publishing
    the rendered result anywhere is a separate question, asked separately, at that time.
    """
    if not ctx.block:
        return ctx
    by = (args.cleared_by or "").strip() or getpass.getuser()
    if args.context_cleared:
        return ctx.cleared_by(by, "--context-cleared")
    roles, calls = _context_spend(args.task, args.critique)
    if not sys.stdin.isatty():
        # Nobody is there to answer. Refusing is the only safe reading of silence.
        raise ValueError(
            f"{_context_summary(ctx, roles, calls)}\n"
            "Nothing was cleared and nothing is interactive here. Re-run with "
            "--context-cleared (and --cleared-by <name>) to send it, or move the files out of "
            "the context folder."
        )
    print(_context_summary(ctx, roles, calls))
    answer = input(f"Send this client material to the provider, on {by}'s name? [y/N] ")
    if answer.strip().lower() not in ("y", "yes"):
        raise ValueError("context not cleared; nothing was sent")
    return ctx.cleared_by(by, "prompt")


def _cmd_run(args) -> int:
    # Assembled before the provider exists, and carried into the run rather than re-read there:
    # the bytes a human clears and the bytes that go out have to be the same bytes.
    ctx = _clear_context(args, engagement.prepare_context(base_root()))
    llm = get_llm(args.provider)
    rec = orchestrator.run(args.task, llm=llm, critique=args.critique, context=ctx)
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
    page = render_dashboard(manifest, d) if args.dashboard else render_run(manifest, d)
    out = Path(args.out) if args.out else d / "run.html"
    out.write_text(page, encoding="utf-8")
    print(f"wrote {out}")
    return 0


# What to actually type, per pending_action. The command answers "what now" with a command,
# not with a word the reader then has to translate.
_NEXT_COMMAND = {
    "wait": "still running; poll `huminloop status {run_id} --json` until it leaves running",
    "resynthesize": "huminloop resynthesize {run_id}",
    "approve": 'huminloop approve {run_id} --by "<name>"',
    "reject": 'huminloop reject {run_id} --by "<name>" --reason "<why>"',
    "done": "nothing; this run is decided",
}


def _cmd_status(args) -> int:
    s = gate.status(args.run_id)
    if args.json:
        # The one contract anything scripting this should read. Never parse the prose below:
        # a status word that changes wording between releases breaks a caller silently.
        print(json.dumps(s, indent=2, sort_keys=True))
        return 0
    print(f"run {s['run_id']}  status: {s['status']}")
    if s["needs_resynthesize"]:
        print("  the Engagement Lead's synthesis came back empty; resynthesize can fix it")
    if s["interrupted"]:
        print("  this run died before it finished; it cannot be approved")
    if s["flagged_roles"]:
        print(f"  flagged for your attention: {', '.join(s['flagged_roles'])}")
    if s["unrevised_roles"]:
        # Named plainly, with no fix offered, because none exists. Silence here would read as
        # "everything was challenged", which is the opposite of what happened.
        print(
            f"  never challenged (the critic call returned nothing): "
            f"{', '.join(s['unrevised_roles'])} — no recovery command exists for this"
        )
    # .get(), not [] — a sixth action added to gate.PENDING_ACTIONS must not crash the one
    # command a human runs to ask what to do next. The test asserts the keys stay in step.
    nxt = _NEXT_COMMAND.get(s["pending_action"], "see `huminloop status {run_id} --json`")
    print(f"  next: {nxt.format(run_id=s['run_id'])}")
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


def _cmd_engagement(args) -> int:
    if args.action == "new":
        try:
            root = engagement.create(args.name, brief=args.brief or "")
        except engagement.EngagementError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        print(f"created {root}")
        print(f"  drop discovery notes and client material into {root / 'context'}/")
        print(f'  then: huminloop --engagement {engagement.slugify(args.name)} run "<task>"')
        return 0
    rows = engagement.list_all()
    if not rows:
        print(f"no engagements in {engagement.engagements_dir()}")
        return 0
    for e in rows:
        if e.get("status") == "corrupt":
            # Named and marked rather than omitted: a row that disappears reads as "you never
            # created it", which is the one thing it definitely does not mean.
            # stdout, inline with the rest, exactly as `pending` prints a corrupt run: a
            # broken engagement is a row in the list, not a side channel.
            print(f"{e['slug']:<24} CORRUPT     {e['error']}")
            continue
        ctx = len(engagement.context_files(engagement.path_for(e["slug"])))
        print(f"{e['slug']:<24} {e['created_at'][:10]}  {ctx} context file(s)  {e['name']}")
    return 0


def _cmd_serve(args) -> int:
    from . import server

    server.serve(port=args.port, open_browser=not args.no_open)
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
        "--engagement",
        help="work inside an existing client engagement in ~/Cowork/Engagements "
        '(create one with `huminloop engagement new "<name>"`)',
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
    s.add_argument(
        "--context-cleared",
        action="store_true",
        help="confirm this engagement's context/ may be sent to the model provider "
        "(for scripts; interactively you are asked)",
    )
    s.add_argument(
        "--cleared-by",
        help="name recorded as having cleared the context (default: the OS user)",
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

    s = sub.add_parser(
        "status", help="what this run needs right now (--json for anything scripting it)"
    )
    s.add_argument("run_id")
    s.add_argument(
        "--json", action="store_true", help="machine-readable; the contract callers should read"
    )
    s.set_defaults(fn=_cmd_status)

    s = sub.add_parser("show", help="print a run's manifest and artifacts")
    s.add_argument("run_id")
    s.set_defaults(fn=_cmd_show)

    s = sub.add_parser(
        "render",
        help="render an approved or pending run to a self-contained HTML report",
    )
    s.add_argument("run_id")
    s.add_argument("--out", help="output path (default: <run_dir>/run.html)")
    s.add_argument(
        "--dashboard",
        action="store_true",
        help="a tabbed working dashboard instead of the narrative report",
    )
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

    s = sub.add_parser("engagement", help="create or list client engagements")
    s.add_argument("action", choices=["new", "list"])
    s.add_argument("name", nargs="?", default="")
    s.add_argument("--brief", help="one line on what this engagement is")
    s.set_defaults(fn=_cmd_engagement)

    s = sub.add_parser("serve", help="open the review inbox in a browser (localhost only)")
    s.add_argument("--port", type=int, default=8765)
    s.add_argument("--no-open", action="store_true", help="do not launch a browser")
    s.set_defaults(fn=_cmd_serve)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )
    try:
        load_dotenv(Path(args.env_file))
        root = args.root
        if getattr(args, "engagement", None):
            if root:
                # They mean different roots. Silently letting one win would run client work
                # into a directory the operator did not name.
                raise ValueError(
                    "--root and --engagement both set a run root; pass one or the other"
                )
            # An engagement folder *is* a run root: same out/ and logs/ layout, plus the parts
            # that outlive a single run (context, documents, the brief).
            root = str(engagement.resolve_root(engagement.slugify(args.engagement)))
        if root:
            # --root wins over anything .env says, including absolute ARTIFACT_DIR/LOG_DIR.
            os.environ[ROOT_ENV] = root
            os.environ[ARTIFACT_DIR_ENV] = DEFAULT_ARTIFACT_DIR
            os.environ[LOG_DIR_ENV] = DEFAULT_LOG_DIR
        return args.fn(args)
    except (
        gate.GateError,
        engagement.EngagementError,
        RenderError,
        StorageError,
        ValueError,
        RuntimeError,
        OSError,
    ) as exc:
        if args.verbose:
            raise
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
