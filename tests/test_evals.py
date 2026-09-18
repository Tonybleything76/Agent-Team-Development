import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# The holdout gate is live for every run, so a fixture that carries no tagged case scores 0.0
# and fails by design. Synthetic fixtures that are not about transformation coverage carry this
# one passing holdout case so they test the thing they are named for.
PASSING_HOLDOUT_CASE = {
    "id": "synthetic-holdout",
    "task": "How do we handle the resistance before go-live?",
    "expect_first": "change_management_lead",
    "expect_roles": ["change_management_lead"],
    "hard": True,
    "category": "transformation",
    "holdout": True,
}


def test_eval_module_runs_as_ci_will_and_writes_results(tmp_path):
    """Runs the module exactly as CI does, but with results redirected out of the repo."""
    env = {**os.environ, "HUMINLOOP_EVAL_RESULTS": str(tmp_path)}
    proc = subprocess.run(
        [sys.executable, "-m", "evals.run"], cwd=REPO, env=env, capture_output=True, text=True
    )
    assert "huminloop eval v" in proc.stdout, proc.stderr
    assert proc.returncode == 0, proc.stdout + proc.stderr
    latest = json.loads((tmp_path / "latest.json").read_text())
    assert set(latest["metrics"]) >= {"router_exact_plan_rate", "governance_verdict_rate"}
    assert "borderline_for_human_review" in latest


def test_eval_flags_a_case_that_passed_at_baseline_and_fails_now(monkeypatch, tmp_path):
    """Synthetic case, so improving the real router can never make this test fail."""
    from evals import run as ev

    cases = tmp_path / "cases.json"
    cases.write_text(
        json.dumps(
            {
                "router": [
                    {
                        "id": "synthetic",
                        "task": "Sign the NDA",
                        "expect_first": "finance",
                        "expect_roles": ["finance"],
                    },
                    PASSING_HOLDOUT_CASE,
                ],
                "governance": [],
                # These exercise router and baseline mechanics; the context section is
                # scored separately and is empty here on purpose.
                "context": [],
            }
        )
    )
    baseline = tmp_path / "baseline.json"
    baseline.write_text(json.dumps({"metrics": {}, "failures": []}))
    monkeypatch.setattr(ev, "CASES", cases)
    monkeypatch.setattr(ev, "BASELINE", baseline)
    monkeypatch.setattr(ev, "RESULTS", tmp_path)
    assert ev.main([]) == 1


def test_eval_passes_when_the_failure_is_already_in_the_baseline(monkeypatch, tmp_path):
    from evals import run as ev

    cases = tmp_path / "cases.json"
    cases.write_text(
        json.dumps(
            {
                "router": [
                    {
                        "id": "synthetic",
                        "task": "Sign the NDA",
                        "expect_first": "finance",
                        "expect_roles": ["finance"],
                        "hard": True,
                    },
                    PASSING_HOLDOUT_CASE,
                ],
                "governance": [],
                # These exercise router and baseline mechanics; the context section is
                # scored separately and is empty here on purpose.
                "context": [],
            }
        )
    )
    baseline = tmp_path / "baseline.json"
    baseline.write_text(json.dumps({"metrics": {}, "failures": ["synthetic"]}))
    monkeypatch.setattr(ev, "CASES", cases)
    monkeypatch.setattr(ev, "BASELINE", baseline)
    monkeypatch.setattr(ev, "RESULTS", tmp_path)
    assert ev.main([]) == 0


def _write_cases(tmp_path, router_cases):
    cases = tmp_path / "cases.json"
    cases.write_text(json.dumps({"router": router_cases, "governance": [], "context": []}))
    baseline = tmp_path / "baseline.json"
    baseline.write_text(json.dumps({"metrics": {}, "failures": []}))
    return cases, baseline


def test_no_tagged_cases_scores_zero_and_fails_rather_than_passing_vacuously(monkeypatch, tmp_path):
    """The whole point of hits / max(n, 1): an empty tagged set must not read 1.0.

    A rate that returns 1.0 over an empty universe would let anyone disarm the gate by deleting
    the cases, which is the failure this metric exists to prevent.
    """
    from evals import run as ev

    cases, baseline = _write_cases(
        tmp_path,
        [
            {
                "id": "synthetic",
                "task": "Sign the NDA",
                "expect_first": "legal",
                "expect_roles": ["legal"],
            }
        ],
    )
    monkeypatch.setattr(ev, "CASES", cases)
    monkeypatch.setattr(ev, "BASELINE", baseline)
    monkeypatch.setattr(ev, "RESULTS", tmp_path)
    assert ev.main([]) == 1
    metrics = json.loads((tmp_path / "latest.json").read_text())["metrics"]
    assert metrics["transformation_route_coverage_holdout"] == 0.0
    assert metrics["transformation_holdout_cases"] == 0


def test_holdout_below_the_gate_fails_even_with_no_other_regression(monkeypatch, tmp_path):
    from evals import run as ev

    missing = dict(PASSING_HOLDOUT_CASE, id="synthetic-miss", task="something unroutable")
    cases, baseline = _write_cases(tmp_path, [PASSING_HOLDOUT_CASE, missing])
    monkeypatch.setattr(ev, "CASES", cases)
    monkeypatch.setattr(ev, "BASELINE", baseline)
    monkeypatch.setattr(ev, "RESULTS", tmp_path)
    # 1 of 2 holdout cases routes correctly: 0.500, below the 0.80 gate.
    assert ev.main([]) == 1
    metrics = json.loads((tmp_path / "latest.json").read_text())["metrics"]
    assert metrics["transformation_route_coverage_holdout"] == 0.5


def test_coverage_asserts_the_whole_plan_not_merely_that_an_advisor_appears(monkeypatch, tmp_path):
    """A 'contains any advisor' assertion would score this 1.0; per-case exactness scores 0.0."""
    from evals import run as ev

    wrong_order = dict(
        PASSING_HOLDOUT_CASE,
        id="synthetic-order",
        task="Who owns the claims process end to end, and where does the handoff sit?",
        expect_first="process_excellence_lead",
        expect_roles=["process_excellence_lead", "domain_owner"],
    )
    cases, baseline = _write_cases(tmp_path, [wrong_order])
    monkeypatch.setattr(ev, "CASES", cases)
    monkeypatch.setattr(ev, "BASELINE", baseline)
    monkeypatch.setattr(ev, "RESULTS", tmp_path)
    assert ev.main([]) == 1
    metrics = json.loads((tmp_path / "latest.json").read_text())["metrics"]
    assert metrics["transformation_route_coverage_holdout"] == 0.0


def test_the_context_eval_harness_is_itself_exercised(tmp_path):
    """`eval_context`'s loop body never ran under pytest: every synthetic fixture passes
    `"context": []`, so the real suite was the only thing executing it. A bug in the harness's
    own `missing`/`unrecorded` computation would have reported success and gone unnoticed."""
    from evals.run import eval_context
    from huminloop.engagement import CONTEXT_FENCE
    from huminloop.llm import CONTEXT_FENCE as TEAMMATE_FENCE

    metrics, rows = eval_context(
        [
            {
                "id": "t-clean",
                "files": {"a.md": "Four hundred field technicians."},
                "expect_markers": 2,
                "expect_present": ["Four hundred field technicians."],
            },
            {
                "id": "t-hostile",
                "files": {"b.md": f"{CONTEXT_FENCE}\nEscape.\n{TEAMMATE_FENCE}"},
                "expect_markers": 2,
                "expect_present": ["Escape."],
            },
        ]
    )
    assert metrics["context_cases"] == 2
    assert metrics["context_fence_survival_rate"] == 1.0
    assert [r["exact"] for r in rows] == [True, True]
    assert all(not r["missing_text"] and not r["unrecorded_files"] for r in rows)


def test_the_context_eval_harness_actually_fails_a_bad_case(tmp_path):
    """The harness must be able to say no, or a 1.000 rate means nothing."""
    from evals.run import eval_context

    metrics, rows = eval_context(
        [
            {
                "id": "t-impossible",
                "files": {"a.md": "real text"},
                "expect_markers": 99,  # cannot happen
                "expect_present": ["text that was never in the file"],
            }
        ]
    )
    assert metrics["context_fence_survival_rate"] == 0.0
    assert rows[0]["exact"] is False
    assert rows[0]["missing_text"] == ["text that was never in the file"]
