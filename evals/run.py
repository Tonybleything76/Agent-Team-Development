"""Scored eval for the router and governance checker.

Usage:  python -m evals.run [--set-baseline]
Writes evals/results/latest.json (git-ignored). Regression is judged per case against the
committed baseline.json: any case that passed at baseline and fails now fails the run, and case
counts may not shrink. Rates are reported, not gated, with one exception:
transformation_route_coverage_holdout must stay at or above HOLDOUT_COVERAGE_GATE, because it is
the only number here measured against language the router's keywords were not written from.
Cases marked "borderline" never pass silently: they are listed for a human to check regardless
of outcome.
"""

import argparse
import json
import os
import sys
from pathlib import Path

from huminloop import __version__
from huminloop.governance import review_text
from huminloop.llm import DryRunLLM, build_prompt
from huminloop.orchestrator import produce
from huminloop.personas import load_house_brief, load_persona, persona_keys
from huminloop.roles import SPECIALISTS, get_role
from huminloop.router import Router
from huminloop.storage import now_iso

HERE = Path(__file__).parent
CASES = HERE / "cases.json"
# Tests point this at a temp dir so the suite never writes into the working tree.
RESULTS = Path(os.getenv("HUMINLOOP_EVAL_RESULTS", HERE / "results"))
BASELINE = HERE / "results" / "baseline.json"  # always the committed one
# Counts that may never shrink between baseline and now (deleting or relabelling cases is a
# regression). Pass/fail is compared per case id, so adding an honest failing hard case is fine,
# but a case that passed at baseline and fails now is not.
GATED_COUNTS = (
    "router_cases",
    "router_easy_cases",
    "governance_cases",
    "dryrun_specialists",
    "personas_written",
    "personas_well_formed",
    "specialists_receiving_house_brief",
)
# Transformation coverage carries its own anti-shrink guard rather than being folded into
# GATED_COUNTS, which is left exactly as it was. Deleting tagged cases already drives the rate
# toward 0.0 via hits / max(n, 1), but deleting the *failing* ones would raise it, so the case
# counts are guarded too. Checked alongside GATED_COUNTS in main().
TRANSFORMATION_GATED_COUNTS = ("transformation_cases", "transformation_holdout_cases")
# The holdout is the only gated rate. Below this the eval exits non-zero: the keyword router is
# no longer routing language it has not been shown, and semantic routing is back in scope.
HOLDOUT_COVERAGE_GATE = 0.80
HOW_MEASURED = {
    "router_exact_plan_rate": "share of router cases whose full ordered plan equals the expected",
    "router_easy_exact_rate": "same, over cases that contain a rule keyword (regression guard)",
    "router_hard_exact_rate": "same, over realistic ambiguous cases; expected to be well below 1.0",
    "router_first_role_rate": "share of router cases whose first dispatched role matches",
    "governance_verdict_rate": "share of governance cases with the expected APPROVE/REVISE verdict",
    "governance_issue_recall": "share of governance cases where every expected issue was reported",
    "dryrun_specialists_governance_clean": "share of specialists whose dry-run output passes",
    "personas_written": "specialist roles with a persona file",
    "personas_well_formed": "personas that carry the required sections and reach the prompt",
    "persona_coverage": "personas_written divided by the number of specialist roles",
    "specialists_receiving_house_brief": "specialists whose prompt carries the shared house brief",
    "transformation_route_coverage": (
        "share of cases tagged category=transformation whose full ordered plan equals the "
        "expected one; per-case, not 'contains an advisor'"
    ),
    "transformation_route_coverage_derived": (
        "same, over the extraction subset the routing vocabulary was written from. Expected to "
        "be high by construction and therefore NOT evidence the router generalises"
    ),
    "transformation_route_coverage_holdout": (
        "same, over the holdout subset that was not read while deriving vocabulary. This is the "
        f"only gated rate: below {HOLDOUT_COVERAGE_GATE:.2f} the run fails"
    ),
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
        "router_hard_passing": sum(r["exact"] for r in hard),
        "router_cases": n,
        "router_easy_cases": len(easy),
        "router_hard_cases": len(hard),
        **transformation_coverage(cases, rows),
    }, rows


def transformation_coverage(cases: list[dict], rows: list[dict]) -> dict:
    """Coverage over the transformation cases, reported whole / derived / holdout.

    A case counts as covered only when its full ordered plan matches `expect_roles` — the same
    bar every other router rate uses. "Contains at least one advisor" would be gameable: a
    single broad keyword would satisfy nearly every tagged case with the wrong first role.

    Rates are hits / max(n, 1), matching eval_governance. An empty tagged set therefore reads
    0.0 and fails the gate rather than passing vacuously on an empty universe.
    """
    tagged = [
        (c, r) for c, r in zip(cases, rows, strict=True) if c.get("category") == "transformation"
    ]
    holdout = [(c, r) for c, r in tagged if c.get("holdout")]
    derived = [(c, r) for c, r in tagged if not c.get("holdout")]

    def rate(subset):
        return sum(r["exact"] for _, r in subset) / max(len(subset), 1)

    return {
        "transformation_route_coverage": rate(tagged),
        "transformation_route_coverage_derived": rate(derived),
        "transformation_route_coverage_holdout": rate(holdout),
        "transformation_cases": len(tagged),
        "transformation_holdout_cases": len(holdout),
    }


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
        "governance_verdict_rate": verdict_ok / max(n, 1),
        "governance_issue_recall": issues_ok / max(n, 1),
        "governance_cases": n,
    }, rows


# A persona that cannot say no is a persona that will agree with whoever asked. "Refuse or
# escalate" is gated alongside the other two because it is the section that makes a specialist
# an advisor rather than a generator: it names the work this seat declines to do.
PERSONA_SECTIONS = ("## Remit", "## Output contract", "## Refuse or escalate")


def eval_personas() -> tuple[dict, list[dict]]:
    """Personas are prose, so this checks structure and wiring, not writing quality."""
    rows = []
    house = load_house_brief() or ""
    for key in persona_keys():
        text = load_persona(key) or ""
        system, _ = build_prompt(get_role(key), "eval task", "")
        missing = [s for s in PERSONA_SECTIONS if s not in text]
        rows.append(
            {
                "id": f"persona:{key}",
                "role": key,
                "in_prompt": text in system,
                "sections_ok": not missing,
                "missing_sections": missing,
                "chars": len(text),
                "borderline": False,
            }
        )
    ok = sum(r["in_prompt"] and r["sections_ok"] for r in rows)
    # The house brief must reach every specialist, personified or not.
    housed = sum(house in build_prompt(get_role(k), "eval task", "")[0] for k in SPECIALISTS)
    return {
        "personas_written": len(rows),
        "personas_well_formed": ok,
        "persona_coverage": len(rows) / len(SPECIALISTS),
        "specialists_receiving_house_brief": housed,
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
    p_metrics, p_rows = eval_personas()
    e_metrics = eval_dry_run_end_to_end()
    metrics = {**r_metrics, **g_metrics, **p_metrics, **e_metrics}
    borderline = [x for x in r_rows + g_rows if x["borderline"]]
    failures = (
        [x for x in r_rows if not x["exact"]]
        + [x for x in g_rows if not (x["verdict_ok"] and x["issues_ok"])]
        + [x for x in p_rows if not (x["in_prompt"] and x["sections_ok"])]
    )

    result = {
        "version": __version__,
        "ran_at": now_iso(),
        "how_measured": HOW_MEASURED,
        "metrics": metrics,
        "failures": failures,
        "borderline_for_human_review": borderline,
        "router_rows": r_rows,
        "governance_rows": g_rows,
        "persona_rows": p_rows,
    }
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "latest.json").write_text(json.dumps(result, indent=2))

    print(f"huminloop eval v{__version__}")
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

    failed_ids = {f["id"] for f in failures}
    hard_ids = {r["id"] for r in r_rows if r["hard"]}

    # Gated before the baseline branch on purpose: a below-gate holdout must not be recordable
    # as the new normal. If this fires after two honest passes at vocabulary extraction, the
    # keyword router has hit its ceiling and semantic routing has earned its way back into scope.
    holdout_rate = metrics["transformation_route_coverage_holdout"]
    if holdout_rate < HOLDOUT_COVERAGE_GATE:
        print(
            f"  GATE FAILED: transformation_route_coverage_holdout {holdout_rate:.3f} "
            f"< {HOLDOUT_COVERAGE_GATE:.2f} over {metrics['transformation_holdout_cases']} "
            f"holdout case(s)"
        )
        return 1

    if args.set_baseline:
        if (failed_ids - hard_ids) and not args.allow_failures:
            print("  refusing to set a baseline with failures (use --allow-failures to override)")
            return 1
        BASELINE.write_text(
            json.dumps(
                {
                    "version": __version__,
                    "ran_at": result["ran_at"],
                    "how_measured": HOW_MEASURED,
                    "gated": (
                        "per-case pass->fail transitions, "
                        f"transformation_route_coverage_holdout >= {HOLDOUT_COVERAGE_GATE:.2f}, "
                        "plus " + ", ".join(GATED_COUNTS + TRANSFORMATION_GATED_COUNTS)
                    ),
                    "metrics": metrics,
                    "failures": sorted(failed_ids),
                    "borderline_for_human_review": [b["id"] for b in borderline],
                },
                indent=2,
            )
        )
        print(f"  baseline written to {BASELINE}")
        return 0
    if not BASELINE.exists():
        print("  no baseline yet (run with --set-baseline)")
        return 1 if (failed_ids - hard_ids) else 0
    base = json.loads(BASELINE.read_text())
    newly_failing = sorted(failed_ids - set(base.get("failures", [])))
    shrunk = {
        k: (base["metrics"][k], metrics.get(k, 0))
        for k in GATED_COUNTS + TRANSFORMATION_GATED_COUNTS
        if k in base["metrics"] and metrics.get(k, 0) < base["metrics"][k]
    }
    if newly_failing or shrunk:
        print(f"  REGRESSION vs baseline: newly failing {newly_failing}, shrunk counts {shrunk}")
        return 1
    print("  no regression vs baseline")
    return 0


if __name__ == "__main__":
    sys.exit(main())
