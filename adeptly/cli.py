import argparse
import json
import logging
import os
import sys
from pathlib import Path

from . import __version__, gate, orchestrator
from .llm import PROVIDERS, get_llm
from .roles import ROLES
from .storage import ROOT_ENV, STATES, StorageError, artifact_root, find_run, read_manifest


def load_dotenv(path: Path) -> None:
    """Minimal .env loader: KEY=value lines, '#' comments; never overrides the real environment."""
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip().removeprefix("export ").strip(), value.strip()
        if value[:1] in ("'", '"'):
            quote = value[0]
            end = value.find(quote, 1)
            value = value[1:end] if end > 0 else value[1:]
        else:
            value = value.split(" #", 1)[0].split("\t#", 1)[0].strip()
        if key and key not in os.environ:
            os.environ[key] = value


def _cmd_run(args) -> int:
    llm = get_llm(args.provider)
    rec = orchestrator.run(args.task, llm=llm)
    print(f"run_id: {rec.run_id}  provider: {rec.provider}")
    print(f"plan:   {rec.plan['roles']}  (rules: {rec.plan['matched_rules'] or 'default'})")
    for a in rec.artifacts:
        if a.error:
            print(f"  {a.role:<18} ERROR   {a.error}")
        else:
            issues = "; ".join(a.review["issues"]) if a.review["issues"] else ""
            print(f"  {a.role:<18} {a.review['verdict']:<8} {a.file}  {issues}")
    print(f"status: pending -> review with `adeptly show {rec.run_id}`, then approve or reject.")
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
        status = m.get("status", "")
        flag = "" if status in STATES else f"  [{status}]"
        task = m.get("task", "")[:50]
        print(f"{m['run_id']}  {m.get('created_at', ''):<25} {task!r} {verdicts}{flag}")
    return 0


def _cmd_show(args) -> int:
    found = find_run(artifact_root(None), args.run_id)
    if not found:
        print(f"run {args.run_id} not found", file=sys.stderr)
        return 1
    state, d = found
    print(json.dumps(read_manifest(d), indent=2))
    for f in sorted(d.glob("*.md")):
        print(f"\n===== {state}/{f.name} =====\n{f.read_text(encoding='utf-8')}")
    return 0


def _cmd_approve(args) -> int:
    m = gate.approve(args.run_id, args.by, args.note or "", force=args.force)
    print(f"approved {m['run_id']} by {m['decision']['by']}")
    return 0


def _cmd_reject(args) -> int:
    m = gate.reject(args.run_id, args.by, args.reason)
    print(f"rejected {m['run_id']} by {m['decision']['by']}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="adeptly", description="Hierarchical agent team with a human approval gate"
    )
    p.add_argument("--version", action="version", version=f"adeptly {__version__}")
    p.add_argument("-v", "--verbose", action="store_true")
    p.add_argument(
        "--root",
        help="directory holding out/ and logs/ (default: $ADEPTLY_ROOT or current directory)",
    )
    p.add_argument(
        "--env-file",
        default=os.getenv("ADEPTLY_ENV_FILE", ".env"),
        help="dotenv file to load (default: $ADEPTLY_ENV_FILE or .env)",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("run", help="route a task to specialists and park output in pending/")
    s.add_argument("task")
    s.add_argument("--provider", choices=PROVIDERS)
    s.set_defaults(fn=_cmd_run)

    sub.add_parser("roles", help="list the team").set_defaults(fn=_cmd_roles)

    s = sub.add_parser("pending", help="list runs awaiting a human decision")
    s.add_argument("--state", default="pending", choices=STATES)
    s.set_defaults(fn=_cmd_pending)

    s = sub.add_parser("show", help="print a run's manifest and artifacts")
    s.add_argument("run_id")
    s.set_defaults(fn=_cmd_show)

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
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )
    if args.root:
        os.environ[ROOT_ENV] = args.root
    try:
        load_dotenv(Path(args.env_file))
        return args.fn(args)
    except (gate.GateError, StorageError, ValueError, RuntimeError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
