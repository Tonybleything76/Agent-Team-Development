import json

import pytest

from adeptly import gate, orchestrator
from adeptly.storage import artifact_root, log_path


def _run(llm, task="Define KPIs"):
    return orchestrator.run(task, llm=llm)


def test_approve_moves_run_and_records_decision(workdir, fake_llm):
    rec = _run(fake_llm)
    m = gate.approve(rec.run_id, by="Tony")
    assert m["status"] == "approved" and m["decision"]["by"] == "Tony"
    assert (artifact_root() / "approved" / rec.run_id / "manifest.json").exists()
    assert not (artifact_root() / "pending" / rec.run_id).exists()
    events = [json.loads(line)["event"] for line in log_path().read_text().splitlines()]
    assert events[-1] == "approved"


def test_approve_requires_a_named_person(workdir, fake_llm):
    rec = _run(fake_llm)
    with pytest.raises(gate.GateError):
        gate.approve(rec.run_id, by="  ")


def test_cannot_decide_twice(workdir, fake_llm):
    rec = _run(fake_llm)
    gate.approve(rec.run_id, by="Tony")
    with pytest.raises(gate.GateError, match="already approved"):
        gate.reject(rec.run_id, by="Tony", reason="changed my mind")


def test_reject_requires_reason(workdir, fake_llm):
    rec = _run(fake_llm)
    with pytest.raises(gate.GateError):
        gate.reject(rec.run_id, by="Tony", reason="")


def test_unknown_run_is_refused(workdir):
    with pytest.raises(gate.GateError, match="not found"):
        gate.approve("nope", by="Tony")


class FlaggedLLM:
    name = "flagged"

    def generate(self, system, prompt):
        return "Objective: x\nBody: y\nRisks: ...\nNext Steps: z\n"  # no URL, placeholder


def test_governance_flagged_run_needs_force_and_note(workdir):
    rec = _run(FlaggedLLM())
    assert not rec.all_approved_by_governance
    with pytest.raises(gate.GateError, match="governance flagged"):
        gate.approve(rec.run_id, by="Tony")
    with pytest.raises(gate.GateError, match="requires a --note"):
        gate.approve(rec.run_id, by="Tony", force=True)
    m = gate.approve(rec.run_id, by="Tony", note="reviewed by hand", force=True)
    assert m["decision"]["note"] == "reviewed by hand"


def test_list_runs_by_state(workdir, fake_llm):
    a, b = _run(fake_llm), _run(fake_llm)
    gate.reject(b.run_id, by="Tony", reason="dup")
    assert [m["run_id"] for m in gate.list_runs("pending")] == [a.run_id]
    assert [m["run_id"] for m in gate.list_runs("rejected")] == [b.run_id]
