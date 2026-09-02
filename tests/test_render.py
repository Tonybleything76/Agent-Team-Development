"""huminloop/render.py: the HTML report for an approved run.

Two kinds of test here. Pure-function tests check the small parsing/formatting helpers in
isolation with hand-built input. The end-to-end tests build a real manifest and real artifact
files on disk (either via orchestrator.run()+gate.approve(), or by copying the committed
docs/example-run/synthesis/ fixture) and render them, because escaping and section-boundary bugs
only show up against the real envelope shape — a hand-typed unit fixture would not have caught
the parse_registers bug that motivated this module's Escalations handling.
"""

import json
import shutil
from pathlib import Path

import pytest

from huminloop import gate, orchestrator
from huminloop.render import (
    RenderError,
    _register_group,
    _split_decision,
    artifact_doc_html,
    esc,
    render_run,
    split_headline,
)
from huminloop.storage import artifact_root
from tests.conftest import RecordingLLM

FIXTURE_DIR = Path(__file__).resolve().parents[1] / "docs" / "example-run" / "synthesis"

# --------------------------------------------------------------------------- pure functions


def test_split_headline_prefers_a_trailing_question():
    task = "The pilot cleared its floor. Two workstreams are behind. What do we decide first?"
    headline, context = split_headline(task)
    assert headline == "What do we decide first?"
    assert context == "The pilot cleared its floor. Two workstreams are behind."


def test_split_headline_falls_back_to_the_leading_sentence():
    task = "Scale the copilot to member services. Data quality is poor and unresolved."
    headline, context = split_headline(task)
    assert headline == "Scale the copilot to member services."
    assert context == "Data quality is poor and unresolved."


def test_split_headline_one_sentence_has_no_context():
    headline, context = split_headline("Draft an RFP response and SOW")
    assert headline == "Draft an RFP response and SOW"
    assert context == ""


def test_split_headline_never_invents_or_drops_words():
    """The split must be a pure partition of the task's own sentences — nothing paraphrased,
    nothing lost — since an audit record must not show text the run never actually said."""
    task = "First sentence here. Second one too. Is this the real question?"
    headline, context = split_headline(task)
    assert headline == "Is this the real question?"
    assert context == "First sentence here. Second one too."


def test_split_decision_separates_owner():
    text, owner = _split_decision("Who owns override review? -> domain_owner")
    assert text == "Who owns override review?"
    assert owner == "domain_owner"


def test_split_decision_without_owner_is_none():
    text, owner = _split_decision("Who owns override review?")
    assert text == "Who owns override review?"
    assert owner is None


def test_esc_escapes_html_and_quotes():
    assert esc("<script>alert('x')</script>") == (
        "&lt;script&gt;alert(&#x27;x&#x27;)&lt;/script&gt;"
    )
    assert esc(None) == ""


def test_artifact_doc_html_escapes_and_never_interprets_markup():
    text = (
        "Objective: Decide <b>fast</b> & correctly.\n\n"
        "Body: The plan is real.\n\n"
        "Citations:\n- https://example.com/a\n- https://example.com/b\n\n"
        "Risks: None material.\n\n"
        "Next Steps:\n1. Do the thing.\n2. Then the other thing.\n"
    )
    out = artifact_doc_html(text)
    assert "<b>fast</b>" not in out  # the model's own markup is data, never rendered as HTML
    assert "&lt;b&gt;fast&lt;/b&gt;" in out
    assert "&amp;" in out
    assert '<a href="https://example.com/a">https://example.com/a</a>' in out
    assert "<ol>" in out and "<li>Do the thing.</li>" in out


def test_register_group_none_reads_as_none_not_a_bare_zero():
    html = _register_group("Escalations", [])
    assert ">None<" in html


# --------------------------------------------------------------------------- refusal rules


def test_render_refuses_a_pending_run(workdir, fake_llm):
    rec = orchestrator.run("Draft an RFP response and SOW", llm=fake_llm)
    d = artifact_root() / "pending" / rec.run_id
    manifest = json.loads((d / "manifest.json").read_text())
    with pytest.raises(RenderError, match="not approved"):
        render_run(manifest, d)


def test_render_refuses_a_run_with_tampered_artifact_bytes(workdir, fake_llm):
    rec = orchestrator.run("Draft an RFP response and SOW", llm=fake_llm)
    gate.approve(rec.run_id, by="Tony")
    d = artifact_root() / "approved" / rec.run_id
    manifest = json.loads((d / "manifest.json").read_text())
    first_file = next(a["file"] for a in manifest["artifacts"] if a.get("file"))
    (d / first_file).write_text("tampered content", encoding="utf-8")
    with pytest.raises(gate.GateError, match="changed since"):
        render_run(manifest, d)


# --------------------------------------------------------------------------- wiring


def test_render_a_real_approved_run_end_to_end(workdir, fake_llm):
    rec = orchestrator.run("Draft an RFP response and SOW", llm=fake_llm)
    gate.approve(rec.run_id, by="Tony", note="looks right")
    d = artifact_root() / "approved" / rec.run_id
    manifest = json.loads((d / "manifest.json").read_text())
    page = render_run(manifest, d)
    assert page.startswith("<!doctype html>")
    assert '<section id="routing">' in page
    assert '<section id="decision"' in page
    assert "Tony" in page


def test_render_shows_an_errored_specialist_as_absent_not_missing(workdir):
    failing = RecordingLLM(fail_roles=["legal"])
    rec = orchestrator.run("Draft an RFP response and SOW", llm=failing)
    gate.approve(rec.run_id, by="Tony", force=True, note="known gap, approving anyway")
    d = artifact_root() / "approved" / rec.run_id
    manifest = json.loads((d / "manifest.json").read_text())
    page = render_run(manifest, d)
    assert 'id="a-legal"' in page
    assert "This seat produced nothing" in page


def test_render_via_cli(workdir, fake_llm, monkeypatch, capsys):
    import huminloop.cli as cli

    monkeypatch.setattr(cli, "get_llm", lambda provider=None: fake_llm)
    assert cli.main(["run", "Draft an RFP response and SOW"]) == 0
    run_id = capsys.readouterr().out.split("run_id: ")[1].split()[0]
    assert cli.main(["approve", run_id, "--by", "Tony"]) == 0
    assert cli.main(["render", run_id]) == 0
    out = capsys.readouterr().out
    assert "wrote" in out
    written = artifact_root() / "approved" / run_id / "run.html"
    assert written.exists()
    assert written.read_text(encoding="utf-8").startswith("<!doctype html>")


def test_render_via_cli_refuses_pending(workdir, fake_llm, monkeypatch, capsys):
    import huminloop.cli as cli

    monkeypatch.setattr(cli, "get_llm", lambda provider=None: fake_llm)
    assert cli.main(["run", "Draft an RFP response and SOW"]) == 0
    run_id = capsys.readouterr().out.split("run_id: ")[1].split()[0]
    assert cli.main(["render", run_id]) == 2
    err = capsys.readouterr().err
    assert "not approved" in err


# --------------------------------------------------------------------------- the real example


def test_render_the_committed_synthesis_example(tmp_path):
    """The regression fixture: the actual 8-advisor + Engagement Lead run this module was
    built against, including its corrected 3-escalation register. Copied to a tmp dir with a
    matching run_id so read_manifest's directory-name check is satisfied like a real run."""
    manifest = json.loads((FIXTURE_DIR / "manifest.json").read_text())
    d = tmp_path / manifest["run_id"]
    shutil.copytree(FIXTURE_DIR, d)
    page = render_run(manifest, d)

    assert page.count("<section") == 19  # routing + 8×(critique+artifact) + synthesis + decision
    assert '<span class="register-count">6</span>' in page  # Decisions
    assert '<span class="register-count">2</span>' in page  # Disagreements
    assert '<span class="register-count">3' in page  # Escalations, "3 — forces this approval"
    assert "gate forced" in page
    assert "decision forced" in page
    assert "What do we need to decide before go-live?" in page
    assert "healthcare operations team" in page  # the context paragraph, not lost
    # No stray Next Steps text leaked into the Escalations register (the bug this fixes):
    escalations_idx = page.index('<h3>Escalations</h3>')
    escalations_html = page[escalations_idx : escalations_idx + 2000]
    assert "classification memo" not in escalations_html
