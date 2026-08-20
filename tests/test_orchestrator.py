import json

import pytest

from adeptly import orchestrator
from adeptly.governance import review_text
from adeptly.llm import DryRunLLM
from adeptly.roles import SPECIALISTS
from adeptly.storage import artifact_root, log_path
from tests.conftest import RecordingLLM


def test_run_writes_manifest_and_one_artifact_per_specialist(workdir, fake_llm):
    rec = orchestrator.run("Draft an RFP response and SOW", llm=fake_llm)
    d = artifact_root() / "pending" / rec.run_id
    manifest = json.loads((d / "manifest.json").read_text())
    assert manifest["plan"]["roles"] == ["pre_sales", "legal", "finance"]
    assert sorted(p.name for p in d.glob("*.md")) == ["finance.md", "legal.md", "pre_sales.md"]
    assert manifest["status"] == "pending" and manifest["provider"] == "fake"


def test_prior_output_is_passed_as_context_to_later_specialists(workdir, fake_llm):
    orchestrator.run("Draft an RFP response and SOW", llm=fake_llm)
    first_prompt, second_prompt = fake_llm.calls[0][1], fake_llm.calls[1][1]
    assert "Prior work from teammates" not in first_prompt
    assert "[Pre-Sales]" in second_prompt


def test_one_failing_specialist_does_not_hide_the_others(workdir):
    llm = RecordingLLM(fail_roles=["Legal"])
    rec = orchestrator.run("Draft an RFP response and SOW", llm=llm)
    by_role = {a.role: a for a in rec.artifacts}
    assert by_role["legal"].error and by_role["legal"].file is None
    assert by_role["pre_sales"].file == "pre_sales.md" and by_role["finance"].file == "finance.md"
    events = [json.loads(line) for line in log_path().read_text().splitlines()]
    assert any(e["event"] == "specialist_error" and e["role"] == "legal" for e in events)
    assert events[-1]["event"] == "run_end" and events[-1]["errors"] == 1


def test_manifest_exists_from_the_start_and_tracks_progress(workdir):
    from adeptly.storage import artifact_root

    class Spy:
        name = "spy"

        def __init__(self):
            self.seen = []

        def generate(self, system, prompt):
            # Capture the manifest status while a specialist is "running".
            d = next((artifact_root() / "pending").iterdir())
            self.seen.append(json.loads((d / "manifest.json").read_text())["status"])
            return "Objective: t\nBody: b\nCitations: https://x.io\nRisks: r\nNext Steps: n\n"

    spy = Spy()
    rec = orchestrator.run("Draft an RFP response and SOW", llm=spy)
    assert spy.seen == ["running", "running", "running"]
    final = json.loads((artifact_root() / "pending" / rec.run_id / "manifest.json").read_text())
    assert final["status"] == "pending" and len(final["artifacts"]) == 3


def test_empty_task_is_rejected(workdir, fake_llm):
    with pytest.raises(ValueError):
        orchestrator.run("   ", llm=fake_llm)


def test_supervisor_roles_cannot_be_dispatched(workdir, fake_llm):
    with pytest.raises(ValueError):
        orchestrator.produce("governance", "task", fake_llm)


@pytest.mark.parametrize("role_key", sorted(SPECIALISTS))
def test_dry_run_output_passes_governance_for_every_specialist(role_key):
    text, review = orchestrator.produce(role_key, "any task at all", DryRunLLM())
    assert review.ok, (role_key, review.issues)
    assert review_text(text).ok
