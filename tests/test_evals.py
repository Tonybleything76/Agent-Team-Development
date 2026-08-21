import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def test_eval_module_runs_as_ci_will_and_writes_results(tmp_path):
    """Runs the module exactly as CI does, but with results redirected out of the repo."""
    env = {**os.environ, "ADEPTLY_EVAL_RESULTS": str(tmp_path)}
    proc = subprocess.run(
        [sys.executable, "-m", "evals.run"], cwd=REPO, env=env, capture_output=True, text=True
    )
    assert "adeptly eval v" in proc.stdout, proc.stderr
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
                    }
                ],
                "governance": [],
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
                    }
                ],
                "governance": [],
            }
        )
    )
    baseline = tmp_path / "baseline.json"
    baseline.write_text(json.dumps({"metrics": {}, "failures": ["synthetic"]}))
    monkeypatch.setattr(ev, "CASES", cases)
    monkeypatch.setattr(ev, "BASELINE", baseline)
    monkeypatch.setattr(ev, "RESULTS", tmp_path)
    assert ev.main([]) == 0
