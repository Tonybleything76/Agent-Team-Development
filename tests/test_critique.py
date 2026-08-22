import pytest

from huminloop import gate, orchestrator
from huminloop.critique import (
    Critique,
    CritiquePoint,
    apply_responses,
    extract_revision,
    parse_critique,
)
from huminloop.llm import Completion
from huminloop.storage import artifact_root

GOOD = (
    "Objective: a real objective\nBody: a real body with content\nCitations: https://x.io/a\n"
    "Risks: a real risk\nNext Steps: a real step\n"
)


def test_parse_extracts_steelman_premortem_and_points():
    c = parse_critique(
        "STEELMAN: The case is coherent because it sequences spend behind evidence.\n"
        "PREMORTEM: It failed because the baseline was never measured.\n"
        "POINT: blocking | evidence | The 25% figure has no source\n"
        "POINT: minor | consistency | Phase 2 dates contradict Phase 1\n",
        "qa_qc",
    )
    assert "sequences spend" in c.steelman and "baseline" in c.premortem
    assert [p.severity for p in c.points] == ["blocking", "minor"]
    assert c.points[0].dimension == "evidence"
    assert "25%" in c.points[0].claim


def test_unknown_severity_or_dimension_degrades_instead_of_dropping_the_finding():
    c = parse_critique("POINT: catastrophic | vibes | something is wrong here", "qa_qc")
    assert len(c.points) == 1
    assert c.points[0].severity == "serious" and c.points[0].dimension == "consistency"
    assert "something is wrong" in c.points[0].claim


def test_responses_attach_and_unanswered_points_stay_unresolved():
    c = Critique(
        "qa_qc",
        points=[
            CritiquePoint("blocking", "evidence", "a"),
            CritiquePoint("minor", "consistency", "b"),
        ],
    )
    apply_responses(c, "RESPONSE 1: ACCEPTED — added the source\nREVISED:\nnew text\n")
    assert c.points[0].disposition == "accepted" and not c.points[0].unresolved
    assert c.points[1].disposition is None and c.points[1].unresolved
    assert extract_revision("RESPONSE 1: ACCEPTED — x\nREVISED:\nnew text\n") == "new text"


class ScriptedLLM:
    """Plays the critic and the author in turn so the loop can be tested end to end."""

    name = "scripted"

    def __init__(self, critic_text, author_text):
        self.critic_text, self.author_text = critic_text, author_text
        self.roles = []

    def generate(self, system, prompt, role=None):
        self.roles.append(role)
        if "reviewing a teammate's draft" in system:
            return Completion(self.critic_text)
        if "A reviewer has challenged your draft" in system:
            return Completion(self.author_text)
        return Completion(GOOD)


def test_accepted_critique_produces_a_revised_artifact(workdir):
    llm = ScriptedLLM(
        "STEELMAN: s\nPREMORTEM: p\nPOINT: serious | evidence | no source for the claim\n",
        "RESPONSE 1: ACCEPTED — added the source\nREVISED:\n"
        + GOOD.replace("Body: a real body with content", "Body: a real body, now with a source"),
    )
    rec = orchestrator.run("Define KPIs", llm=llm)
    art = rec.artifacts[0]
    assert art.revised is True
    assert art.critique["points"][0]["disposition"] == "accepted"
    assert "now with a source" in (artifact_root() / "pending" / rec.run_id / art.file).read_text()
    assert art.review["verdict"] == "APPROVE"


def test_dismissing_a_blocking_critique_costs_a_named_human_a_written_note(workdir):
    """Suppressing dissent stays possible and never silent."""
    llm = ScriptedLLM(
        "STEELMAN: s\nPREMORTEM: p\nPOINT: blocking | evidence | the core number is unsourced\n",
        "RESPONSE 1: REJECTED — I stand by it\nREVISED:\n" + GOOD,
    )
    rec = orchestrator.run("Define KPIs", llm=llm)
    art = rec.artifacts[0]
    assert art.critique["points"][0]["disposition"] == "rejected"
    # The dismissal is a fact about the process, not the bytes, so it rides in process_flags
    # and still forces a human to take responsibility at the gate.
    assert any("Unresolved blocking critique" in f for f in art.process_flags)
    assert not rec.all_approved_by_governance

    with pytest.raises(gate.GateError, match="governance flagged"):
        gate.approve(rec.run_id, by="Tony")
    m = gate.approve(rec.run_id, by="Tony", force=True, note="critic overreached, shipping")
    assert m["decision"]["forced"] is True


def test_a_critic_that_finds_nothing_does_not_manufacture_a_revision(workdir):
    llm = ScriptedLLM("STEELMAN: s\nPREMORTEM: p\n", "unused")
    rec = orchestrator.run("Define KPIs", llm=llm)
    assert rec.artifacts[0].revised is False
    assert rec.artifacts[0].critique["points"] == []


def test_a_failing_critic_never_loses_the_draft(workdir):
    class BrokenCritic(ScriptedLLM):
        def generate(self, system, prompt, role=None):
            if "reviewing a teammate's draft" in system:
                raise RuntimeError("critic provider down")
            return Completion(GOOD)

    rec = orchestrator.run("Define KPIs", llm=BrokenCritic("", ""))
    art = rec.artifacts[0]
    assert art.file and art.error is None and art.critique is None
    assert art.review["verdict"] == "APPROVE"


def test_the_critic_role_is_not_critiqued_by_itself(workdir, fake_llm):
    rec = orchestrator.run("Write the PRD with user stories and acceptance criteria", llm=fake_llm)
    assert "qa_qc" in rec.plan["roles"]
    qa = next(a for a in rec.artifacts if a.role == "qa_qc")
    assert qa.critique is None and qa.file
