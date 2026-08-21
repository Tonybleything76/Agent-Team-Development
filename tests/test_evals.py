import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def test_eval_module_runs_as_ci_will_and_writes_results():
    proc = subprocess.run(
        [sys.executable, "-m", "evals.run"], cwd=REPO, capture_output=True, text=True
    )
    assert "adeptly eval v" in proc.stdout, proc.stderr
    assert proc.returncode == 0, proc.stdout + proc.stderr
    latest = json.loads((REPO / "evals" / "results" / "latest.json").read_text())
    assert set(latest["metrics"]) >= {"router_exact_plan_rate", "governance_verdict_rate"}
    assert "borderline_for_human_review" in latest


def test_eval_detects_a_newly_failing_case(monkeypatch, tmp_path):
    from evals import run as ev

    # Point the baseline at a copy that claims h05 passed, so the current h05 failure is "new".
    base = json.loads(ev.BASELINE.read_text())
    base["failures"] = []
    fake = tmp_path / "baseline.json"
    fake.write_text(json.dumps(base))
    monkeypatch.setattr(ev, "BASELINE", fake)
    monkeypatch.setattr(ev, "RESULTS", tmp_path)
    assert ev.main([]) == 1
