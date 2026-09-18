"""The Engagement Lead: what the pipeline owes it, and what it owes the human.

A note on what these tests can and cannot prove. With a fake provider we can assert that the
lead RECEIVES everything it needs to see a disagreement, and that whatever it reports is
carried faithfully to the gate. We cannot assert that a real model actually names a conflict it
was shown; that is a property of the model, and the committed example run is the evidence for
it. Tests that claim otherwise would be theatre.
"""

import json
import os
from pathlib import Path

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


def test_escalations_body_stops_before_the_envelope_next_steps():
    """The registers live inside the outer envelope's Body: section. Escalations is always the
    last register, so its body capture must stop at Citations:/Risks:/Next Steps: — not run on
    and absorb Next Steps' own numbered lines as escalations. Real bug: a genuine 3-item
    Escalations register was reported as 7 because it swallowed 4 Next Steps items."""
    text = (
        "Objective: Decide whether to scale.\n\n"
        "Body:\n\n"
        "## Recommendation\nHold the rollout.\n\n"
        "## Decisions\n1. Who owns override review? -> domain_owner\n\n"
        "## Disagreements\nNone.\n\n"
        "## Escalations\n"
        "1. Does the union agreement permit the role change?\n"
        "2. Is there a deadline driving this?\n"
        "3. Will leadership state headcount impact explicitly?\n\n"
        "Citations:\n- https://example.com/a\n\n"
        "Risks: Unaddressed classification gap.\n\n"
        "Next Steps:\n"
        "1. Legal issues a classification memo.\n"
        "2. Sponsor names an owner.\n"
        "3. Data lead profiles the extract.\n"
        "4. Change lead runs interviews.\n"
    )
    regs = parse_registers(text)
    assert len(regs["escalations"]) == 3
    assert "union agreement" in regs["escalations"][0]
    assert not any("classification memo" in e for e in regs["escalations"])


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


def test_resynthesize_recovers_a_failed_synthesis_without_rerunning_specialists(workdir, fake_llm):
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


# ---------------------------------------------------------------------------
# What a resynthesize must not destroy, and what it must not silently re-read.
# ---------------------------------------------------------------------------


def _engagement_run(tmp_path, monkeypatch, llm, task="Draft an RFP response and SOW"):
    """A run inside an engagement that has real context, cleared and sent."""
    from huminloop import engagement

    monkeypatch.setenv(engagement.ENGAGEMENTS_ENV, str(tmp_path / "Engagements"))
    root = engagement.create("Acme")
    (root / "context" / "discovery.md").write_text("400 field techs. Union caps training hours.")
    monkeypatch.setenv("HUMINLOOP_ROOT", str(root))
    monkeypatch.setenv("ARTIFACT_DIR", "out")
    monkeypatch.setenv("LOG_DIR", "logs")
    ctx = engagement.prepare_context(root).cleared_by("Tony", "test")
    return root, orchestrator.run(task, llm=llm, context=ctx)


def test_resynthesize_keeps_the_record_of_what_the_team_was_given(tmp_path, monkeypatch):
    """It used to rebuild the record without context_read, and write_manifest then overwrote a
    real audit record with []: the run's account of what client material it saw, destroyed by
    the command meant to rescue it."""
    failing = RecordingLLM(fail_roles=("engagement_lead",))
    root, rec = _engagement_run(tmp_path, monkeypatch, failing)
    assert [c["file"] for c in rec.context_read] == ["discovery.md"]

    again = orchestrator.resynthesize(rec.run_id, llm=RecordingLLM())
    assert [c["file"] for c in again.context_read] == ["discovery.md"]
    assert again.context_clearance["by"] == "Tony"

    on_disk = json.loads((artifact_root() / "pending" / rec.run_id / "manifest.json").read_text())
    assert [c["file"] for c in on_disk["context_read"]] == ["discovery.md"]
    assert on_disk["context_clearance"]["by"] == "Tony"


def test_a_run_snapshots_the_context_it_was_given(tmp_path, monkeypatch):
    from huminloop import engagement

    root, rec = _engagement_run(tmp_path, monkeypatch, RecordingLLM())
    snapshot = artifact_root() / "pending" / rec.run_id / "context" / "context.md"
    assert snapshot.is_file()
    assert "Union caps training hours" in snapshot.read_text()
    # And it is evidence, not an artifact: `show` and the Documents tab glob *.md at the top
    # level of the run directory and must not pick it up.
    assert "context.md" not in [p.name for p in (snapshot.parent.parent).glob("*.md")]
    assert engagement.read_snapshot(snapshot.parent.parent) == snapshot.read_text()


def test_the_snapshot_survives_the_context_folder_changing_underneath(tmp_path, monkeypatch):
    """A resynthesize an hour later must not integrate different client material than the
    specialists saw."""
    from huminloop import engagement

    failing = RecordingLLM(fail_roles=("engagement_lead",))
    root, rec = _engagement_run(tmp_path, monkeypatch, failing)
    (root / "context" / "discovery.md").write_text("Completely different client, different facts.")

    d = artifact_root() / "pending" / rec.run_id
    assert "Union caps training hours" in engagement.read_snapshot(d)
    assert "Completely different" not in engagement.read_snapshot(d)


# ---------------------------------------------------------------------------
# resynthesize is a second door into the provider (found 2026-09-17, pre-landing review).
# ---------------------------------------------------------------------------


def test_resynthesize_refuses_a_snapshot_nobody_cleared(workdir):
    """A run that never had engagement context would accept a context.md dropped into its
    directory afterwards and send it, with context_clearance still null in the manifest."""
    from huminloop.engagement import EngagementError

    failing = RecordingLLM(fail_roles=("engagement_lead",))
    rec = orchestrator.run("Define KPIs and a dashboard", llm=failing, critique=False)
    d = artifact_root() / "pending" / rec.run_id
    assert json.loads((d / "manifest.json").read_text())["context_clearance"] is None

    (d / "context").mkdir(exist_ok=True)
    (d / "context" / "context.md").write_text("SMUGGLED client material nobody approved")

    retry = RecordingLLM()
    with pytest.raises(EngagementError, match="nobody cleared"):
        orchestrator.resynthesize(rec.run_id, llm=retry)
    assert retry.calls == []  # refused before the provider, not after


def test_resynthesize_refuses_a_snapshot_edited_since_it_was_cleared(tmp_path, monkeypatch):
    """Otherwise material changed after approval goes out under the approver's name."""
    from huminloop.engagement import EngagementError

    failing = RecordingLLM(fail_roles=("engagement_lead",))
    root, rec = _engagement_run(tmp_path, monkeypatch, failing)
    d = artifact_root() / "pending" / rec.run_id
    (d / "context" / "context.md").write_text("TAMPERED after Tony signed for it")

    retry = RecordingLLM()
    with pytest.raises(EngagementError, match="changed since Tony cleared it"):
        orchestrator.resynthesize(rec.run_id, llm=retry)
    assert retry.calls == []


def test_an_untampered_resynthesize_still_carries_the_cleared_material(tmp_path, monkeypatch):
    """The gate must not break the path it exists to protect."""
    failing = RecordingLLM(fail_roles=("engagement_lead",))
    root, rec = _engagement_run(tmp_path, monkeypatch, failing)
    retry = RecordingLLM()
    orchestrator.resynthesize(rec.run_id, llm=retry)
    lead = next(
        p for (_, p), r in zip(retry.calls, retry.roles, strict=True) if r == "engagement_lead"
    )
    assert "Union caps training hours" in lead


@pytest.mark.parametrize("sabotage", ["delete", "empty", "unreadable"])
def test_resynthesize_refuses_when_the_cleared_snapshot_is_gone(tmp_path, monkeypatch, sabotage):
    """Failing open here is the silent omission the gate exists to stop: the manifest still
    asserts a named human cleared the material, and the lead would quietly rewrite the
    client-facing recommendation having been given none of it."""
    import os as _os

    from huminloop.engagement import EngagementError

    if sabotage == "unreadable" and (_os.name != "posix" or _os.geteuid() == 0):
        pytest.skip("chmod-based test requires an unprivileged POSIX user")

    failing = RecordingLLM(fail_roles=("engagement_lead",))
    root, rec = _engagement_run(tmp_path, monkeypatch, failing)
    snap = artifact_root() / "pending" / rec.run_id / "context" / "context.md"

    if sabotage == "delete":
        snap.unlink()
    elif sabotage == "empty":
        snap.write_text("")
    else:
        snap.chmod(0o000)

    retry = RecordingLLM()
    try:
        with pytest.raises(EngagementError, match="missing or empty"):
            orchestrator.resynthesize(rec.run_id, llm=retry)
        assert retry.calls == []
    finally:
        if sabotage == "unreadable":
            snap.chmod(0o644)


def test_resynthesize_refuses_a_lost_snapshot_even_with_no_clearance_recorded(workdir):
    """The guard originally keyed on `clearance` alone, so the hole stayed open through the
    null-clearance branch: context_read still advertised the files as read while the lead was
    rewritten having been given nothing."""
    from huminloop.engagement import EngagementError

    failing = RecordingLLM(fail_roles=("engagement_lead",))
    rec = orchestrator.run("Define KPIs and a dashboard", llm=failing, critique=False)
    d = artifact_root() / "pending" / rec.run_id
    m = json.loads((d / "manifest.json").read_text())
    m["context_read"] = [{"chars": 35, "file": "client.md", "state": "read"}]
    m["context_clearance"] = None
    (d / "manifest.json").write_text(json.dumps(m))

    retry = RecordingLLM()
    with pytest.raises(EngagementError, match="snapshot is missing or empty"):
        orchestrator.resynthesize(rec.run_id, llm=retry)
    assert retry.calls == []


def test_no_test_in_this_file_runs_the_orchestrator_outside_a_temp_root():
    """A test without `workdir` leaves HUMINLOOP_ROOT unset, so `base_root()` falls back to
    Path(".") -- the run writes into the repo and would read ./context/ if one existed. One
    test in this file did exactly that. Pin it so the next one cannot."""
    import re

    src = Path(__file__).read_text()
    offenders = []
    for block in re.split(r"\n(?=def test_|@pytest)", src):
        m = re.search(r"def (test_\w+)\(([^)]*)\)", block, re.S)
        if not m or "orchestrator.run(" not in block:
            continue
        if "workdir" not in m.group(2) and "_engagement_run(" not in block:
            offenders.append(m.group(1))
    assert offenders == [], f"these run the orchestrator without an isolated root: {offenders}"
