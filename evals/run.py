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
# Metrics that may not drop below the baseline. Rates that include the deliberately hard router
# cases are reported but not gated, so adding an honest failing hard case is never a regression.
GATED_METRICS = (
    "router_easy_exact_rate",
    "governance_verdict_rate",
    "governance_issue_recall",
    "dryrun_specialists_governance_clean",
    "router_cases",
    "router_hard_cases",
    "governance_cases",
    "dryrun_specialists",
)
HOW_MEASURED = {
    "router_exact_plan_rate": "share of router cases whose full ordered plan equals the expected",
    "router_easy_exact_rate": "same, over cases that contain a rule keyword (regression guard)",
    "router_hard_exact_rate": "same, over realistic ambiguous cases; expected to be well below 1.0",
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
                "hard": bool(c.get("hard")),
                "note": c.get("note", ""),
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
    hard = [r for r, c in zip(rows, cases, strict=True) if c.get("hard")]
    easy = [r for r, c in zip(rows, cases, strict=True) if not c.get("hard")]
    return {
        "router_exact_plan_rate": exact / n,
        "router_first_role_rate": first / n,
        "router_easy_exact_rate": sum(r["exact"] for r in easy) / max(len(easy), 1),
        "router_hard_exact_rate": sum(r["exact"] for r in hard) / max(len(hard), 1),
        "router_cases": n,
        "router_hard_cases": len(hard),
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
    ap.add_argument(
        "--allow-failures",
        action="store_true",
        help="with --set-baseline: record a baseline even though some cases fail",
    )
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

    # Hard cases are allowed to fail (that is the point of them); easy cases are not.
    hard_ids = {r["id"] for r in r_rows if r["hard"]}
    blocking = [f for f in failures if f["id"] not in hard_ids]

    if args.set_baseline:
        if blocking and not args.allow_failures:
            print("  refusing to set a baseline with failures (use --allow-failures to override)")
            return 1
        BASELINE.write_text(
            json.dumps(
                {
                    "version": __version__,
                    "ran_at": result["ran_at"],
                    "how_measured": HOW_MEASURED,
                    "gated_metrics": list(GATED_METRICS),
                    "metrics": metrics,
                    "failures": [f["id"] for f in failures],
                    "borderline_for_human_review": [b["id"] for b in borderline],
                },
                indent=2,
            )
        )
        print(f"  baseline written to {BASELINE}")
        return 0
    if BASELINE.exists():
        base = json.loads(BASELINE.read_text())["metrics"]
        # Gated rates must not drop; case counts must not shrink (deleting cases is a regression).
        regressions = {
            k: (base[k], metrics.get(k, 0))
            for k in GATED_METRICS
            if k in base and metrics.get(k, 0) < base[k]
        }
        if regressions:
            print(f"  REGRESSION vs baseline: {regressions}")
            return 1
        print("  no regression vs baseline")
    else:
        print("  no baseline yet (run with --set-baseline)")
    return 1 if blocking else 0


if __name__ == "__main__":
    sys.exit(main())
