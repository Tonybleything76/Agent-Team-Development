"""Scored eval for the router and governance checker.

Usage:  python -m evals.run [--set-baseline]
Writes evals/results/latest.json (and a timestamped copy). Exits 1 if any metric falls below the
committed baseline, so CI catches regressions. Cases marked "borderline" never pass silently: they
are listed for a human to check regardless of outcome.
"""

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from adeptly import __version__
from adeptly.governance import review_text
from adeptly.llm import DryRunLLM
from adeptly.orchestrator import produce
from adeptly.roles import SPECIALISTS
from adeptly.router import Router

HERE = Path(__file__).parent
CASES = HERE / "cases.json"
RESULTS = HERE / "results"
BASELINE = RESULTS / "baseline.json"
HOW_MEASURED = {
    "router_exact_plan_rate": "share of router cases whose full ordered plan equals the expected",
    "router_first_role_rate": "share of router cases whose first dispatched role matches",
    "governance_verdict_rate": "share of governance cases with the expected APPROVE/REVISE verdict",
    "governance_issue_recall": "share of governance cases where every expected issue was reported",
    "dryrun_specialists_governance_clean": "share of specialists whose dry-run output passes",
}


def eval_router(cases: list[dict]) -> tuple[dict, list[dict]]:
    router = Router()
    rows, exact, first = [], 0, 0
    for c in cases:
        plan = router.route(c["task"])
        ok_exact = plan.roles == c["expect_roles"]
        ok_first = bool(plan.roles) and plan.roles[0] == c["expect_first"]
        exact += ok_exact
        first += ok_first
        rows.append(
            {
                "id": c["id"],
                "task": c["task"],
                "expected": c["expect_roles"],
                "got": plan.roles,
                "rules": plan.matched_rules,
                "exact": ok_exact,
                "first_role_ok": ok_first,
                "borderline": bool(c.get("borderline")) or (ok_first and not ok_exact),
            }
        )
    n = len(cases)
    return {
        "router_exact_plan_rate": exact / n,
        "router_first_role_rate": first / n,
        "router_cases": n,
    }, rows


def eval_governance(cases: list[dict]) -> tuple[dict, list[dict]]:
    rows, verdict_ok, issues_ok = [], 0, 0
    for c in cases:
        r = review_text(c["text"])
        v_ok = r.verdict == c["expect_verdict"]
        i_ok = all(i in r.issues for i in c["expect_issues"])
        verdict_ok += v_ok
        issues_ok += i_ok
        rows.append(
            {
                "id": c["id"],
                "expected_verdict": c["expect_verdict"],
                "got_verdict": r.verdict,
                "expected_issues": c["expect_issues"],
                "got_issues": r.issues,
                "verdict_ok": v_ok,
                "issues_ok": i_ok,
                "borderline": bool(c.get("borderline")) or (v_ok and not i_ok),
                "note": c.get("note", ""),
            }
        )
    n = len(cases)
    return {
        "governance_verdict_rate": verdict_ok / n,
        "governance_issue_recall": issues_ok / n,
        "governance_cases": n,
    }, rows


def eval_dry_run_end_to_end() -> dict:
    llm = DryRunLLM()
    clean = sum(produce(k, "eval task", llm)[1].ok for k in SPECIALISTS)
    return {
        "dryrun_specialists_governance_clean": clean / len(SPECIALISTS),
        "dryrun_specialists": len(SPECIALISTS),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--set-baseline", action="store_true", help="write current metrics as baseline")
    args = ap.parse_args(argv)

    cases = json.loads(CASES.read_text())
    r_metrics, r_rows = eval_router(cases["router"])
    g_metrics, g_rows = eval_governance(cases["governance"])
    e_metrics = eval_dry_run_end_to_end()
    metrics = {**r_metrics, **g_metrics, **e_metrics}
    borderline = [x for x in r_rows + g_rows if x["borderline"]]
    failures = [x for x in r_rows if not x["exact"]] + [
        x for x in g_rows if not (x["verdict_ok"] and x["issues_ok"])
    ]

    result = {
        "version": __version__,
        "ran_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "how_measured": HOW_MEASURED,
        "metrics": metrics,
        "failures": failures,
        "borderline_for_human_review": borderline,
        "router_rows": r_rows,
        "governance_rows": g_rows,
    }
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "latest.json").write_text(json.dumps(result, indent=2))
    stamp = result["ran_at"].replace(":", "").replace("-", "")
    (RESULTS / f"run_{stamp}.json").write_text(json.dumps(result, indent=2))

    print(f"adeptly eval v{__version__}")
    for k, v in metrics.items():
        print(f"  {k:<40} {v:.3f}" if isinstance(v, float) else f"  {k:<40} {v}")
    print(f"  failures: {len(failures)}   borderline (human review): {len(borderline)}")
    for b in borderline:
        print(f"    borderline {b['id']}: {b.get('note') or 'partial match'}")
    for f in failures:
        print(
            f"    FAIL {f['id']}: expected {f.get('expected') or f.get('expected_verdict')} "
            f"got {f.get('got') or f.get('got_verdict')}"
        )

    if args.set_baseline:
        BASELINE.write_text(
            json.dumps(
                {"version": __version__, "ran_at": result["ran_at"], "metrics": metrics}, indent=2
            )
        )
        print(f"  baseline written to {BASELINE}")
        return 0
    if BASELINE.exists():
        base = json.loads(BASELINE.read_text())["metrics"]
        regressions = {
            k: (base[k], metrics[k])
            for k in base
            if isinstance(base[k], float) and metrics.get(k, 0) < base[k]
        }
        if regressions:
            print(f"  REGRESSION vs baseline: {regressions}")
            return 1
        print("  no regression vs baseline")
    else:
        print("  no baseline yet (run with --set-baseline)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
