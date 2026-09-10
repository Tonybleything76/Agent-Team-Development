"""The UI adds no rules. These tests exist to prove it cannot become a way around them."""

import json

import pytest

from huminloop import gate, orchestrator, server
from huminloop.storage import artifact_root


@pytest.fixture
def state(workdir):
    return server.ReviewState()


def _run(llm, task="Define KPIs"):
    return orchestrator.run(task, llm=llm, critique=False)


def _flag(run_id, text):
    """Attach a process flag the way an escalating Engagement Lead would."""
    _, d = gate.find_run(artifact_root(), run_id)
    m = gate.read_manifest(d)
    m["artifacts"][0]["process_flags"] = [text]
    gate.write_manifest(d, m)
    return m


def test_escalations_are_separated_from_other_process_flags():
    m = {
        "artifacts": [
            {
                "role": "lead",
                "process_flags": [
                    "Escalated to the human: who owns the backfill budget?",
                    "Output truncated at the token budget (raise LLM_MAX_TOKENS)",
                ],
            }
        ]
    }
    assert server.escalations(m) == ["who owns the backfill budget?"]
    assert server.other_flags(m) == [
        "lead: Output truncated at the token budget (raise LLM_MAX_TOKENS)"
    ]


def test_inbox_lists_pending_runs_and_flags_what_needs_you(state, fake_llm):
    rec = _run(fake_llm)
    _flag(rec.run_id, "Escalated to the human: is the go-live date already committed?")
    page = server.inbox_page(state)
    assert rec.run_id in page and "1 for you" in page


def test_run_page_surfaces_the_escalation_and_the_decision_panel(state, fake_llm):
    rec = _run(fake_llm)
    _flag(rec.run_id, "Escalated to the human: is the go-live date already committed?")
    code, page = server.run_page(state, rec.run_id)
    assert code == 200
    assert "is the go-live date already committed?" in page
    assert "only you can answer" in page
    assert state.token in page  # the form carries the guard


def test_an_unknown_or_malformed_run_id_does_not_leak_a_traceback(state):
    assert server.run_page(state, "20260101_000000_abcdef")[0] == 404
    code, page = server.run_page(state, "../../etc")
    assert code == 400 and "invalid run_id" in page and "Traceback" not in page


def test_the_ui_cannot_approve_a_flagged_run_without_a_forced_override(state, fake_llm):
    """The rule lives in gate.py; the UI must not have its own softer version."""
    rec = _run(fake_llm)
    _flag(rec.run_id, "Escalated to the human: unanswered")
    with pytest.raises(gate.GateError, match="governance flagged"):
        gate.approve(rec.run_id, "Tony", "", root=state.root)
    m = gate.approve(rec.run_id, "Tony", "taking it to the sponsor", force=True, root=state.root)
    assert m["decision"]["forced"] is True


def test_serve_refuses_to_bind_beyond_loopback():
    with pytest.raises(ValueError, match="loopback-only"):
        server.serve(host="0.0.0.0", open_browser=False)


def test_decisions_made_through_the_ui_land_in_the_same_audit_trail(state, fake_llm):
    rec = _run(fake_llm)
    gate.annotate(rec.run_id, "Tony", "a reservation", root=state.root)
    gate.approve(rec.run_id, "Tony", "shipping", root=state.root)
    gate.reopen(rec.run_id, "Tony", "changed my mind", root=state.root)
    _, d = gate.find_run(artifact_root(), rec.run_id)
    m = json.loads((d / "manifest.json").read_text())
    assert [x["state"] for x in m["decisions"]] == ["approved", "reopened"]
    assert m["annotations"][0]["note"] == "a reservation"
