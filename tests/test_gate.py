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
        gate.approve("20260101_000000_abcdef", by="Tony")


def test_path_traversal_run_ids_are_refused(workdir, fake_llm):
    rec = _run(fake_llm)
    gate.approve(rec.run_id, by="Tony")
    for evil in (f"../approved/{rec.run_id}", "../../etc", "nope", "20260101_000000_ABCDEF"):
        with pytest.raises(gate.GateError, match="invalid run_id"):
            gate.reject(evil, by="Mallory", reason="flip it")
    assert gate.find_run(artifact_root(), rec.run_id)[0] == "approved"


def test_run_with_errored_specialist_is_flagged_not_crashing(workdir):
    from tests.conftest import RecordingLLM

    rec = orchestrator.run("Draft an RFP response and SOW", llm=RecordingLLM(fail_roles=["Legal"]))
    with pytest.raises(gate.GateError, match="governance flagged \\['legal'\\]"):
        gate.approve(rec.run_id, by="Tony")
    m = gate.approve(rec.run_id, by="Tony", force=True, note="legal reviewed offline")
    assert m["status"] == "approved"


def test_incomplete_and_corrupt_runs_are_surfaced(workdir, fake_llm):
    rec = _run(fake_llm)
    (artifact_root() / "pending" / "20260101_000000_aaaaaa").mkdir(parents=True)
    (artifact_root() / "pending" / "20260101_000000_bbbbbb").mkdir()
    (artifact_root() / "pending" / "20260101_000000_bbbbbb" / "manifest.json").write_text(
        "{not json"
    )
    statuses = {m["run_id"]: m["status"] for m in gate.list_runs("pending")}
    assert statuses[rec.run_id] == "pending"
    assert statuses["20260101_000000_aaaaaa"].startswith("incomplete")
    assert statuses["20260101_000000_bbbbbb"].startswith("corrupt")


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


def test_failed_force_leaves_no_trace_and_forced_is_recorded(workdir):
    from tests.conftest import RecordingLLM

    rec = orchestrator.run("Draft an RFP response and SOW", llm=RecordingLLM(fail_roles=["Legal"]))
    with pytest.raises(gate.GateError):
        gate.approve(rec.run_id, by="   ", force=True, note="x")  # fails on approver name
    with pytest.raises(gate.GateError, match="governance flagged"):
        gate.approve(rec.run_id, by="Tony")  # plain approve still refused
    m = gate.approve(rec.run_id, by="Tony", force=True, note="legal reviewed offline")
    assert m["decision"]["forced"] is True and m["decision"]["flagged_roles"] == ["legal"]
    events = [json.loads(line) for line in log_path().read_text().splitlines()]
    assert events[-1]["event"] == "approved" and events[-1]["forced"] is True


def test_clean_approval_records_forced_false(workdir, fake_llm):
    rec = _run(fake_llm)
    m = gate.approve(rec.run_id, by="Tony")
    assert m["decision"]["forced"] is False and m["decision"]["flagged_roles"] == []


def test_interrupted_run_can_be_rejected_but_not_approved(workdir, fake_llm):
    rec = _run(fake_llm)
    _, d = gate.find_run(artifact_root(), rec.run_id)
    m = gate.read_manifest(d)
    m["status"] = "running"
    gate.write_manifest(d, m)
    with pytest.raises(gate.GateError, match="interrupted"):
        gate.approve(rec.run_id, by="Tony", force=True, note="x")
    assert gate.reject(rec.run_id, by="Tony", reason="interrupted")["status"] == "rejected"


def test_recorded_decision_cannot_be_overwritten_and_can_be_completed(
    workdir, fake_llm, monkeypatch
):
    import os

    rec = _run(fake_llm)
    real_rename = os.rename
    monkeypatch.setattr(os, "rename", lambda *a, **k: (_ for _ in ()).throw(OSError("disk")))
    with pytest.raises(OSError):
        gate.approve(rec.run_id, by="Tony")
    monkeypatch.setattr(os, "rename", real_rename)
    listed = {m["run_id"]: m["status"] for m in gate.list_runs("pending")}
    assert "decision recorded" in listed[rec.run_id]
    with pytest.raises(gate.GateError, match="already has a recorded approved by Tony"):
        gate.reject(rec.run_id, by="Mallory", reason="nah")
    m = gate.approve(rec.run_id, by="Someone Else")  # completes Tony's recorded decision
    assert m["decision"]["by"] == "Tony" and m["status"] == "approved"


def test_live_run_cannot_be_decided(workdir, fake_llm):
    from adeptly.storage import write_lock

    rec = _run(fake_llm)
    _, d = gate.find_run(artifact_root(), rec.run_id)
    write_lock(d)  # our own pid: alive
    with pytest.raises(gate.GateError, match="still running"):
        gate.reject(rec.run_id, by="Tony", reason="x")
    assert "running (live)" in gate.list_runs("pending")[0]["status"]


def test_malformed_manifest_is_a_gate_error(workdir):
    d = artifact_root() / "pending" / "20260101_000000_cccccc"
    d.mkdir(parents=True)
    (d / "manifest.json").write_text(
        '{"run_id": "20260101_000000_cccccc", "artifacts": [{"file": "x"}]}'
    )
    with pytest.raises(gate.GateError, match="malformed"):
        gate.reject("20260101_000000_cccccc", by="Tony", reason="x")
    assert gate.list_runs("pending")[0]["status"].startswith("corrupt")


def test_orphan_pending_dir_can_be_rejected_but_not_approved(workdir):
    d = artifact_root() / "pending" / "20260101_000000_dddddd"
    d.mkdir(parents=True)
    with pytest.raises(gate.GateError, match="not found"):
        gate.approve("20260101_000000_dddddd", by="Tony", force=True, note="x")
    m = gate.reject("20260101_000000_dddddd", by="Tony", reason="died before first write")
    assert m["status"] == "rejected" and not d.exists()


def test_completing_someone_elses_decision_logs_original_decider(workdir, fake_llm, monkeypatch):
    import os

    rec = _run(fake_llm)
    real = os.rename
    monkeypatch.setattr(os, "rename", lambda *a, **k: (_ for _ in ()).throw(OSError("disk")))
    with pytest.raises(OSError):
        gate.approve(rec.run_id, by="Tony")
    monkeypatch.setattr(os, "rename", real)
    gate.approve(rec.run_id, by="Bea")
    last = json.loads(log_path().read_text().splitlines()[-1])
    assert last["by"] == "Tony" and last["completed_by"] == "Bea"
