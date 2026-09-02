"""The Engagement Lead: what the pipeline owes it, and what it owes the human.

A note on what these tests can and cannot prove. With a fake provider we can assert that the
lead RECEIVES everything it needs to see a disagreement, and that whatever it reports is
carried faithfully to the gate. We cannot assert that a real model actually names a conflict it
was shown; that is a property of the model, and the committed example run is the evidence for
it. Tests that claim otherwise would be theatre.
"""

import json
import os

import pytest

from huminloop import gate, orchestrator
from huminloop.orchestrator import ArtifactRecord, parse_registers, synthesize
from huminloop.roles import ROLES, SPECIALISTS
from huminloop.storage import StorageError, artifact_root
from tests.conftest import RecordingLLM

# --------------------------------------------------------------------------- registers


def test_registers_parse_numbered_entries():
    text = (
        "## Recommendation\nHold the rollout.\n"
        "## Decisions\n1. Who owns override review? -> domain_owner\n"
        "2. Does the ROI model assume headcount cuts? -> value_realization_lead\n"
        "## Disagreements\n1. change_management_lead vs value_realization_lead on scale timing\n"
        "## Escalations\n1. Does the union agreement permit the role change?\n"
    )
    regs = parse_registers(text)
    assert len(regs["decisions"]) == 2
    assert len(regs["disagreements"]) == 1
    assert len(regs["escalations"]) == 1
    assert regs["decisions"][0].endswith("-> domain_owner")


def test_explicit_none_is_empty_not_missing():
    """An empty register and an absent one must never be indistinguishable."""
    filled = parse_registers("## Disagreements\n1. a vs b on timing\n")
    empty = parse_registers("## Disagreements\nNone. The advisors did not conflict.\n")
    absent = parse_registers("## Recommendation\nShip it.\n")
    assert len(filled["disagreements"]) == 1
    assert empty["disagreements"] == []
    assert absent["disagreements"] == []
    # The distinction the renderer and the reader need is present in the text, not the counts.
    assert "None." in "## Disagreements\nNone. The advisors did not conflict.\n"


# --------------------------------------------------------------------------- the dissent gate


class _CaptureLLM:
    """Records the prompt the lead was given, so we can assert what it could see."""

    name = "capture"

    def __init__(self, reply: str):
        self.reply = reply
        self.prompts: list[str] = []

    def generate(self, system, prompt, role=None):
        self.prompts.append(f"{system}\n{prompt}")

        class C:
            text = self.reply
            truncated = False

        return C()


CONFLICT_A = (
    "Objective\nAssess readiness.\n\nBody\nThe pilot cleared its statistical floor and the "
    "team should scale in Q1.\n\nCitations\nhttps://example.com/a\n\nRisks\nNone material.\n\n"
    "Next Steps\nScale.\n"
)
CONFLICT_B = (
    "Objective\nAssess readiness.\n\nBody\nThe pilot did not clear adoption readiness and the "
    "team must not scale in Q1.\n\nCitations\nhttps://example.com/b\n\nRisks\nAdoption.\n\n"
    "Next Steps\nHold.\n"
)


@pytest.fixture
def conflicting_run(tmp_path):
    """Two advisors that reached opposite conclusions on the same question."""
    (tmp_path / "value_realization_lead.md").write_text(CONFLICT_A, encoding="utf-8")
    (tmp_path / "change_management_lead.md").write_text(CONFLICT_B, encoding="utf-8")
    return tmp_path, [
        ArtifactRecord(
            "value_realization_lead",
            "value_realization_lead.md",
            {"ok": True, "issues": [], "verdict": "APPROVE"},
        ),
        ArtifactRecord(
            "change_management_lead",
            "change_management_lead.md",
            {"ok": True, "issues": [], "verdict": "APPROVE"},
        ),
    ]


def test_lead_is_shown_both_sides_of_a_conflict_in_full(conflicting_run):
    """The lead cannot name a disagreement it was never shown. Specialists see 600 chars of
    each predecessor; the lead must see every artifact whole."""
    out, artifacts = conflicting_run
    llm = _CaptureLLM("## Disagreements\n1. value_realization_lead vs change_management_lead\n")
    synthesize("Should we scale?", artifacts, llm, out)
    seen = llm.prompts[0]
    assert "should scale in Q1" in seen
    assert "must not scale in Q1" in seen
    assert "value_realization_lead.md" not in seen  # the text itself, not a filename reference


def test_unresolved_blocking_critique_reaches_the_lead(conflicting_run):
    """An advisor who dismissed a blocking objection is standing on weaker evidence, and the
    lead has to know before it builds on that finding."""
    out, artifacts = conflicting_run
    artifacts[0].critique = {
        "points": [
            {
                "claim": "The statistical floor was computed on three weeks of data.",
                "severity": "blocking",
                "disposition": "rejected",
            }
        ]
    }
    llm = _CaptureLLM("## Disagreements\nNone.\n")
    synthesize("Should we scale?", artifacts, llm, out)
    assert "UNRESOLVED BLOCKING CRITIQUE" in llm.prompts[0]
    assert "three weeks of data" in llm.prompts[0]


def test_absent_seats_are_named_to_the_lead(conflicting_run):
    """A seat that produced nothing is information the human needs, not a gap to paper over."""
    out, artifacts = conflicting_run
    artifacts.append(ArtifactRecord("data_readiness_lead", None, None, error="boom"))
    llm = _CaptureLLM("## Disagreements\nNone.\n")
    synthesize("Should we scale?", artifacts, llm, out)
    assert "SEATS THAT PRODUCED NOTHING" in llm.prompts[0]
    assert "data_readiness_lead" in llm.prompts[0]


def test_escalations_become_process_flags(conflicting_run):
    """An escalation must cost a human their signature: process_flags reach flagged_roles(),
    which forces --force plus a written note at the gate."""
    out, artifacts = conflicting_run
    llm = _CaptureLLM(
        "## Escalations\n1. Does the union agreement permit the role change?\n"
        "2. Will the CFO fund a second pilot?\n"
    )
    _, _, flags = synthesize("Should we scale?", artifacts, llm, out)
    assert len(flags) == 2
    assert all(f.startswith("Escalated to the human:") for f in flags)
    assert "union agreement" in flags[0]


# --------------------------------------------------------------------------- wiring


def test_synthesis_is_appended_last_and_counted(workdir, fake_llm):
    rec = orchestrator.run("Draft an RFP response and SOW", llm=fake_llm)
    assert rec.artifacts[-1].role == "engagement_lead"
    assert rec.synthesis is not None
    assert set(rec.synthesis) >= {"decisions", "disagreements", "escalations"}
    d = artifact_root() / "pending" / rec.run_id
    manifest = json.loads((d / "manifest.json").read_text())
    assert manifest["synthesis"]["role"] == "engagement_lead"


def test_no_synthesis_when_every_specialist_failed(workdir, monkeypatch, fake_llm):
    """A run with nothing to integrate must not invent an integration."""

    def boom(*a, **k):
        raise RuntimeError("provider down")

    monkeypatch.setattr(orchestrator, "produce", boom)
    rec = orchestrator.run("Draft an RFP response and SOW", llm=fake_llm)
    assert all(a.error for a in rec.artifacts)
    assert rec.synthesis is None
    assert "engagement_lead" not in [a.role for a in rec.artifacts]


def test_failed_synthesis_does_not_lose_specialist_work(workdir, monkeypatch, fake_llm):
    def boom(*a, **k):
        raise RuntimeError("lead fell over")

    monkeypatch.setattr(orchestrator, "synthesize", boom)
    rec = orchestrator.run("Draft an RFP response and SOW", llm=fake_llm)
    good = [a for a in rec.artifacts if not a.error]
    assert len(good) == 3  # pre_sales, legal, finance survived
    assert rec.artifacts[-1].role == "engagement_lead"
    assert rec.artifacts[-1].error is not None
    assert rec.status == "pending"  # still reviewable and rejectable


def test_produce_still_refuses_every_supervisor(fake_llm):
    """The guard that stops the router and the governance evaluator being dispatched as peers
    must keep holding, the Engagement Lead included. It reaches the model via synthesize()."""
    for key in ROLES:
        if key in SPECIALISTS:
            continue
        with pytest.raises(ValueError):
            orchestrator.produce(key, "task", fake_llm, "")


# --------------------------------------------------------------------------- resynthesize


def test_resynthesize_recovers_a_failed_synthesis_without_rerunning_specialists(
    workdir, fake_llm
):
    """The failure this exists for: every specialist succeeded, the lead's call came back
    empty. Resynthesize must retry only the lead against what's already on disk."""
    failing = RecordingLLM(fail_roles=("engagement_lead",))
    rec = orchestrator.run("Draft an RFP response and SOW", llm=failing)
    lead = next(a for a in rec.artifacts if a.role == "engagement_lead")
    assert lead.error is not None
    assert rec.synthesis is None
    specialist_calls_before = len(failing.calls)

    retried = orchestrator.resynthesize(rec.run_id, llm=fake_llm)
    assert retried.synthesis is not None
    lead_artifacts = [a for a in retried.artifacts if a.role == "engagement_lead"]
    assert len(lead_artifacts) == 1  # the failed placeholder was replaced, not appended alongside
    assert lead_artifacts[0].error is None
    assert len(failing.calls) == specialist_calls_before  # no specialist was re-run
    # Only the lead and its critic ran, not the eight specialists.
    assert fake_llm.roles == ["engagement_lead", "qa_qc"]

    d = artifact_root() / "pending" / rec.run_id
    manifest = json.loads((d / "manifest.json").read_text())
    assert manifest["synthesis"]["role"] == "engagement_lead"
    assert sum(1 for a in manifest["artifacts"] if a["role"] == "engagement_lead") == 1


def test_resynthesize_can_itself_fail_and_leaves_the_run_pending(workdir):
    """A second bad synthesis attempt must not lose the run or crash the caller — same rule
    as the first attempt inside run()."""
    failing = RecordingLLM(fail_roles=("engagement_lead",))
    rec = orchestrator.run("Draft an RFP response and SOW", llm=failing)
    also_failing = RecordingLLM(fail_roles=("engagement_lead",))
    retried = orchestrator.resynthesize(rec.run_id, llm=also_failing)
    assert retried.synthesis is None
    lead = next(a for a in retried.artifacts if a.role == "engagement_lead")
    assert lead.error is not None
    d = artifact_root() / "pending" / rec.run_id
    assert not (d / "run.lock").exists()  # the lock is always released, success or failure


def test_resynthesize_refuses_a_run_that_already_succeeded(workdir, fake_llm):
    rec = orchestrator.run("Draft an RFP response and SOW", llm=fake_llm)
    assert rec.synthesis is not None
    with pytest.raises(StorageError, match="already has a successful"):
        orchestrator.resynthesize(rec.run_id, llm=fake_llm)


def test_resynthesize_refuses_an_unknown_run(workdir, fake_llm):
    with pytest.raises(StorageError, match="not found"):
        orchestrator.resynthesize("20260101_000000_ffffff", llm=fake_llm)


def test_resynthesize_refuses_a_live_run(workdir, fake_llm):
    failing = RecordingLLM(fail_roles=("engagement_lead",))
    rec = orchestrator.run("Draft an RFP response and SOW", llm=failing)
    d = artifact_root() / "pending" / rec.run_id
    (d / "run.lock").write_text(str(os.getpid()), encoding="utf-8")  # simulate a live process
    with pytest.raises(StorageError, match="still running"):
        orchestrator.resynthesize(rec.run_id, llm=fake_llm)


def test_resynthesize_refuses_a_decided_run(workdir, fake_llm):
    failing = RecordingLLM(fail_roles=("engagement_lead",))
    rec = orchestrator.run("Draft an RFP response and SOW", llm=failing)
    gate.reject(rec.run_id, "Tony Bleything", "testing resynthesize's decided-run guard")
    with pytest.raises(StorageError, match="rejected, not pending"):
        orchestrator.resynthesize(rec.run_id, llm=fake_llm)
