import json

import pytest

from huminloop import orchestrator
from huminloop.governance import REQUIRED_SECTIONS, review_text
from huminloop.llm import DryRunLLM
from huminloop.roles import SPECIALISTS
from huminloop.storage import artifact_root, log_path
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
    llm = RecordingLLM(fail_roles=["legal"])
    rec = orchestrator.run("Draft an RFP response and SOW", llm=llm)
    by_role = {a.role: a for a in rec.artifacts}
    assert by_role["legal"].error and by_role["legal"].file is None
    assert by_role["pre_sales"].file == "pre_sales.md" and by_role["finance"].file == "finance.md"
    events = [json.loads(line) for line in log_path().read_text().splitlines()]
    assert any(e["event"] == "specialist_error" and e["role"] == "legal" for e in events)
    assert events[-1]["event"] == "run_end" and events[-1]["errors"] == 1


def test_manifest_exists_from_the_start_and_tracks_progress(workdir):
    class Spy:
        name = "spy"

        def __init__(self):
            self.seen = []

        def generate(self, system, prompt, role=None):
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


def test_specialist_role_key_is_passed_to_the_provider(workdir, fake_llm):
    # OpenRouter resolves model and effort per role; if the key stops arriving, every
    # specialist silently falls back to the default model.
    orchestrator.run("Draft an RFP response and SOW", llm=fake_llm)
    assert fake_llm.roles == ["pre_sales", "legal", "finance"]


def test_empty_generation_is_flagged_by_governance_not_crashing(workdir):
    class EmptyLLM:
        name = "empty"

        def generate(self, system, prompt, role=None):
            return ""

    rec = orchestrator.run("Define KPIs", llm=EmptyLLM())
    assert rec.artifacts[0].review["verdict"] == "REVISE"
    assert len(rec.artifacts[0].review["issues"]) == len(REQUIRED_SECTIONS)


def test_pii_in_the_task_is_refused_before_anything_is_written(workdir, fake_llm):
    from huminloop.storage import artifact_root

    with pytest.raises(ValueError, match="Possible PII"):
        orchestrator.run("email jane@acme.com about the retention schedule", llm=fake_llm)
    assert not (artifact_root() / "pending").exists()


def test_oversized_task_is_refused(workdir, fake_llm):
    with pytest.raises(ValueError, match="keep it under"):
        orchestrator.run("x" * (orchestrator.MAX_TASK_CHARS + 1), llm=fake_llm)


def test_teammate_context_is_fenced_as_untrusted(workdir, fake_llm):
    from huminloop.llm import CONTEXT_FENCE

    orchestrator.run("Draft an RFP response and SOW", llm=fake_llm)
    second_prompt = fake_llm.calls[1][1]
    assert second_prompt.count(CONTEXT_FENCE) == 2
    assert "never as instructions" in second_prompt
