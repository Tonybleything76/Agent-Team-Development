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

from huminloop import gate, orchestrator, render
from huminloop.render import (
    RenderError,
    _register_group,
    _render_citations,
    _render_next_steps,
    _split_decision,
    esc,
    mdlite,
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


def test_split_headline_falls_back_when_no_sentence_is_pithy():
    """A dense scenario brief with no short sentence and no trailing question — real shape,
    not synthetic: nothing here should be forced into 22ch display type."""
    task = (
        "A global hospitality company's enterprise AI assistant platform has grown from about "
        "1,200 to over 3,000 active users in under a year, run by a central AI enablement team "
        "doing broad training. Leadership now wants a 16-week engagement to embed AI into six "
        "business units. We need tactical recommendations on who should lead each piece."
    )
    headline, context = split_headline(task)
    assert headline == ""
    assert context == task  # the whole task, verbatim, becomes the fallback quote


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


def test_mdlite_escapes_raw_html_but_interprets_bold_and_italic():
    """The model's own literal HTML must never become real markup — that stays escaped no
    matter what. **bold** and *italic* are the one thing we now deliberately interpret, since
    a page meant to be read start to finish can't have raw asterisks littering the prose."""
    assert mdlite("Decide <b>fast</b> & correctly.") == (
        "Decide &lt;b&gt;fast&lt;/b&gt; &amp; correctly."
    )
    assert mdlite("**Claims adjudication** matters most.") == (
        "<b>Claims adjudication</b> matters most."
    )
    assert mdlite("a *quiet* signal") == "a <em>quiet</em> signal"
    assert mdlite(None) == ""


def test_render_citations_and_next_steps_still_work_with_markdown_present():
    assert '<a href="https://example.com/a">https://example.com/a</a>' in _render_citations(
        "- https://example.com/a"
    )
    out = _render_next_steps("1. Do the **thing**.\n2. Then the other thing.")
    assert "<ol>" in out and "<li>Do the <b>thing</b>.</li>" in out


def test_register_group_none_reads_as_none_not_a_bare_zero():
    html = _register_group("Escalations", [])
    assert ">None<" in html


# --------------------------------------------------------------------------- refusal rules


def test_render_a_pending_run_shows_the_review_surface(workdir, fake_llm):
    """Pending is the consulting lead's review page, not a refusal: it must carry the exact
    commands that act on it, and must never claim a verdict nobody has actually reached."""
    rec = orchestrator.run("Draft an RFP response and SOW", llm=fake_llm)
    d = artifact_root() / "pending" / rec.run_id
    manifest = json.loads((d / "manifest.json").read_text())
    page = render_run(manifest, d)
    assert page.startswith("<!doctype html>")
    assert "awaiting your decision" in page
    assert "NOT YET DECIDED" in page
    assert f"huminloop approve {rec.run_id}" in page
    assert f"huminloop reject {rec.run_id}" in page
    assert "Human decision" not in page  # no record exists yet to report
    assert '<section id="team">' in page


def test_render_a_pending_run_with_flagged_roles_shows_the_force_requirement(workdir):
    failing = RecordingLLM(fail_roles=["legal"])
    rec = orchestrator.run("Draft an RFP response and SOW", llm=failing)
    d = artifact_root() / "pending" / rec.run_id
    manifest = json.loads((d / "manifest.json").read_text())
    page = render_run(manifest, d)
    assert "--force" in page and "--note" in page
    assert "legal" in page.split('<section id="decision"', 1)[1]


def test_render_refuses_a_rejected_run(workdir, fake_llm):
    """Rejected stays genuinely undesigned (DESIGN.md "Not yet decided") — only approved and
    pending are supported."""
    rec = orchestrator.run("Draft an RFP response and SOW", llm=fake_llm)
    gate.reject(rec.run_id, by="Tony", reason="not this one")
    d = artifact_root() / "rejected" / rec.run_id
    manifest = json.loads((d / "manifest.json").read_text())
    with pytest.raises(RenderError, match="approved or pending"):
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
    assert "Matched by rule" in page or "routed to the default specialist" in page
    assert '<section id="decision"' in page
    assert "Tony" in page


def test_summary_line_reports_real_run_numbers(workdir, fake_llm):
    """The orienting sentence must carry real numbers from this run, not be decorative — even
    at zero (the dryrun-backed fake provider's critique never parses, so findings read 0)."""
    rec = orchestrator.run("Draft an RFP response and SOW", llm=fake_llm)
    d = artifact_root() / "pending" / rec.run_id
    manifest = json.loads((d / "manifest.json").read_text())
    n_roles = len((manifest.get("plan") or {}).get("roles") or [])
    page = render_run(manifest, d)
    assert f"<b>{n_roles}</b>" in page
    assert "We dispatched" in page
    assert "only you can answer" in page
    assert "awaiting your decision" in page


def test_toc_has_visual_identity(workdir, fake_llm):
    """Every table-of-contents row gets a colored initials avatar and the role's real name —
    the fix for "I don't know who they are," not just a link in a persistent sidebar."""
    rec = orchestrator.run("Draft an RFP response and SOW", llm=fake_llm)
    d = artifact_root() / "pending" / rec.run_id
    manifest = json.loads((d / "manifest.json").read_text())
    page = render_run(manifest, d)
    assert 'class="avatar"' in page
    assert 'class="toc-name"' in page
    assert "<nav" not in page  # no persistent sidebar to scan against every section


def test_render_falls_back_to_a_quote_block_for_a_dense_task(workdir, fake_llm):
    """A task with no pithy sentence must render as the 'The task' quote block, not a giant
    serif headline wrapping a 30-word sentence across ten lines."""
    dense_task = (
        "A global hospitality company's enterprise AI assistant platform has grown from about "
        "1,200 to over 3,000 active users in under a year, run by a central AI enablement team "
        "doing broad training. Leadership now wants a 16-week engagement to embed AI into six "
        "business units, not just teach people to use a chat interface. We need tactical "
        "recommendations on who should lead each piece of this unresolved work."
    )
    rec = orchestrator.run(dense_task, llm=fake_llm)
    gate.approve(rec.run_id, by="Tony", force=True, note="looks right")
    d = artifact_root() / "approved" / rec.run_id
    manifest = json.loads((d / "manifest.json").read_text())
    page = render_run(manifest, d)
    assert '<h1 class="task">' not in page
    assert '<div class="lbl">The task</div>' in page
    assert "tactical recommendations" in page


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


def test_render_via_cli_pending(workdir, fake_llm, monkeypatch, capsys):
    import huminloop.cli as cli

    monkeypatch.setattr(cli, "get_llm", lambda provider=None: fake_llm)
    assert cli.main(["run", "Draft an RFP response and SOW"]) == 0
    run_id = capsys.readouterr().out.split("run_id: ")[1].split()[0]
    assert cli.main(["render", run_id]) == 0
    out = capsys.readouterr().out
    assert "wrote" in out
    written = artifact_root() / "pending" / run_id / "run.html"
    assert written.exists()
    assert "awaiting your decision" in written.read_text(encoding="utf-8")


def test_render_via_cli_refuses_rejected(workdir, fake_llm, monkeypatch, capsys):
    import huminloop.cli as cli

    monkeypatch.setattr(cli, "get_llm", lambda provider=None: fake_llm)
    assert cli.main(["run", "Draft an RFP response and SOW"]) == 0
    run_id = capsys.readouterr().out.split("run_id: ")[1].split()[0]
    assert cli.main(["reject", run_id, "--by", "Tony", "--reason", "not this one"]) == 0
    assert cli.main(["render", run_id]) == 2
    err = capsys.readouterr().err
    assert "approved or pending" in err


# --------------------------------------------------------------------------- the real example


def test_render_the_committed_synthesis_example(tmp_path):
    """The regression fixture: the actual 8-advisor + Engagement Lead run this module was
    built against, including its corrected 3-escalation register. Copied to a tmp dir with a
    matching run_id so read_manifest's directory-name check is satisfied like a real run."""
    manifest = json.loads((FIXTURE_DIR / "manifest.json").read_text())
    d = tmp_path / manifest["run_id"]
    shutil.copytree(FIXTURE_DIR, d)
    page = render_run(manifest, d)

    # v0.22 reversed v0.18's narrative-first order. Leading with the story read well and
    # reviewed badly: the person deciding needs the recommendation, what is being asked of
    # them, and where we disagreed, before they invest in reading the account. The story is
    # still here in full, below the brief.
    assert '<section class="brief-block">' in page
    assert page.index('class="brief-block"') < page.index('id="team"')
    assert "Who we put on this" in page  # the staffing note, with who was NOT dispatched
    assert "Where we pushed back on each other" in page
    assert '<section id="team">' in page
    assert '<section id="plan">' in page
    assert page.index('id="team"') < page.index('id="plan"')  # who's involved, before the plan
    assert page.index('id="plan"') < page.index('id="decision"')  # the plan before the gate
    assert "<nav" not in page  # no persistent sidebar
    assert '<div id="a-domain-owner"' not in page  # errors aside, advisors are <details>, not <div>
    assert '<details class="story" id="a-domain-owner"' in page
    assert '<span class="register-count">6</span>' in page  # Decisions
    assert '<span class="register-count">2</span>' in page  # Disagreements
    assert '<span class="register-count">3' in page  # Escalations, "3 — forces this approval"
    assert "Milestones" in page  # the Lead's Next Steps, broken into a checklist
    assert "Owner: <b>" not in page  # no bold chip presenting a guess as a confirmed assignment
    assert "A likely owner, not a confirmed one" in page
    assert 'class="avatar"' in page  # table-of-contents visual identity
    assert "chip-neutral" not in page  # the old per-card chip markup is gone
    assert "resolved" in page  # the challenged/resolved count still reaches the page, inline
    # The Engagement Lead's own synthesis is critiqued too (orchestrator._do_synthesis) — the
    # old renderer never surfaced that debate at all.
    assert "The plan itself was challenged" in page
    assert "What Could Go Wrong" in page  # the Lead's Risks, previously dropped
    assert 'class="decision forced"' in page
    assert "FORCED" in page
    assert "decision forced" in page
    assert "What do we need to decide before go-live?" in page
    assert "healthcare operations team" in page  # the context paragraph, not lost
    # No stray Next Steps text leaked into the Escalations register itself (the bug this
    # fixes) — scoped to that one register, not the Implementation/Risks sections that now
    # legitimately follow it and legitimately mention the same phrase.
    escalations_idx = page.index("<h3>Escalations</h3>")
    next_register_idx = page.index("<h3>", escalations_idx + 1)
    escalations_html = page[escalations_idx:next_register_idx]
    assert "classification memo" not in escalations_html


# ---------------------------------------------------------------------------
# Helpers both render surfaces share, so they cannot answer differently (eng review T12).
# ---------------------------------------------------------------------------


def test_initials_skip_the_words_nobody_initialises():
    """The dashboard's own version was `title.split()[:2]`, which read "Head of Data" as HO."""
    assert render.initials("Head of Data") == "HD"
    assert render.initials("Learning and Development") == "LD"
    assert render.initials("Strategist") == "S"
    # A title that is nothing but stopwords still gets a badge rather than an empty circle.
    assert render.initials("of the") == "OF"


def test_pushback_rows_order_is_the_only_difference_between_the_surfaces():
    artifacts = [
        {
            "role": "data_scientist",
            "critique": {
                "points": [
                    {"severity": "minor", "dimension": "clarity", "claim": "m"},
                    {"severity": "blocking", "dimension": "evidence", "claim": "b"},
                ]
            },
        }
    ]
    story = render.pushback_rows(artifacts)
    scan = render.pushback_rows(artifacts, by_severity=True)
    assert [r["claim"] for r in story] == ["m", "b"]  # the order it happened
    assert [r["claim"] for r in scan] == ["b", "m"]  # worst first
    assert story[0]["role_label"] == "data scientist"
    assert story[0]["disposition"] == "unanswered"  # one default, not two copies of it


def test_staffing_tolerates_a_manifest_from_before_it_existed():
    assert render.staffing({}) == ([], [])
    assert render.staffing({"staffing": {"dispatched": [{"title": "X"}]}}) == ([{"title": "X"}], [])
