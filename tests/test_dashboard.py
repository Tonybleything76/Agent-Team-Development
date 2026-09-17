"""The dashboard is a working surface, not a document. These pin the parts you scan."""

import json
import shutil
from pathlib import Path

import pytest

from huminloop.dashboard import TABS, _bar, _donut, _is_client_step, _steps, render_dashboard

FIXTURE = Path(__file__).resolve().parents[1] / "docs" / "example-run" / "enablement"
FIXTURES = Path(__file__).resolve().parent / "fixtures"

# Every committed run the dashboard has to survive, and what each one is here to exercise.
# One rich fixture left the empty-state branch of all seven panes unexecuted: the panes that
# matter most on a thin run — the ones that have to say "nothing here yet" rather than render
# an empty shape — were the only ones never rendered.
ALL_RUNS = {
    "rich": FIXTURE,  # 13 challenges, 3 escalations, and no plan.staffing (pre-v0.22)
    "minimal": FIXTURES / "minimal-run",  # no challenges, no escalations, no context
    "failed-synthesis": FIXTURES / "failed-synthesis",  # the Engagement Lead produced nothing
}


def _render(src, tmp_path):
    manifest = json.loads((src / "manifest.json").read_text())
    d = tmp_path / manifest["run_id"]
    shutil.copytree(src, d)
    return render_dashboard(manifest, d)


@pytest.fixture
def page(tmp_path):
    return _render(FIXTURE, tmp_path)


@pytest.fixture
def minimal(tmp_path):
    return _render(ALL_RUNS["minimal"], tmp_path)


@pytest.mark.parametrize("name", sorted(ALL_RUNS))
def test_every_tab_has_a_pane(name, tmp_path):
    page = _render(ALL_RUNS[name], tmp_path)
    for tid, label in TABS:
        assert f'data-t="{tid}"' in page and f'id="p-{tid}"' in page
        assert label in page


@pytest.mark.parametrize("name", sorted(ALL_RUNS))
def test_no_pane_renders_empty(name, tmp_path):
    """An empty-state branch must say something, not collapse to a blank panel."""
    page = _render(ALL_RUNS[name], tmp_path)
    for tid, _ in TABS:
        body = page.split(f'id="p-{tid}">', 1)[1].split("</section>", 1)[0]
        assert body.strip(), f"pane {tid} rendered empty for the {name} run"


def test_escalations_get_a_badge_and_their_own_tab(page):
    assert '<span class="badge">3</span>' in page
    assert "only a human can answer" in page
    assert "go-live date" in page  # the actual escalated question, not a count


def test_the_overview_is_shapes_not_paragraphs(page):
    assert '<div class="bar">' in page  # severity distribution
    assert 'class="ring-fg"' in page  # accepted donut
    assert 'class="tiles"' in page


def test_a_manifest_from_before_the_staffing_note_still_renders(page):
    """The committed fixture predates plan.staffing; an old run must not break the dashboard."""
    assert 'id="p-team"' in page
    assert "Why each was called in" in page


def test_the_team_tab_shows_the_bench_not_just_the_roster(tmp_path):
    manifest = json.loads((FIXTURE / "manifest.json").read_text())
    d = tmp_path / manifest["run_id"]
    shutil.copytree(FIXTURE, d)
    # Staffing is deterministic, so a current run always carries it.
    from huminloop.router import Router

    router = Router()
    plan = router.route(manifest["task"])
    manifest["plan"]["staffing"] = router.staffing(manifest["task"], plan)
    page = render_dashboard(manifest, d)
    assert 'class="people bench"' in page
    assert 'class="person off"' in page  # advisors who were not staffed
    assert "Legal" in page


def test_the_debate_is_collapsed_rows_not_prose(page):
    assert page.count('<details class="pbrow') == 13  # one per challenge, all collapsed
    assert 'class="sev serious"' in page


def test_documents_tab_is_honest_that_drafting_is_not_built(page):
    assert "SOW and RFQ drafting is the next build" in page


def test_bar_and_donut_handle_empty_input():
    assert _bar([]) is not None and "seg" not in _bar([(0, "x", "none")])
    assert "0" in _donut(0, 0, "nothing")  # no division by zero


def test_steps_strips_numbering_and_bullets():
    assert _steps("1. First\n- Second\n\n3) Third") == ["First", "Second", "Third"]


def test_client_steps_are_told_apart_from_yours():
    assert _is_client_step("Sponsor confirms the go-live commitment")
    assert not _is_client_step("Draft the enablement curriculum")


def test_the_dashboard_refuses_a_tampered_artifact(tmp_path):
    """A second render surface is not a way around the integrity check (eng review T1)."""
    from huminloop.gate import GateError

    manifest = json.loads((FIXTURE / "manifest.json").read_text())
    d = tmp_path / manifest["run_id"]
    shutil.copytree(FIXTURE, d)
    artifact = d / manifest["artifacts"][0]["file"]
    artifact.write_text(artifact.read_text() + "\nSmuggled in after the run.\n")
    with pytest.raises(GateError, match="changed since the run"):
        render_dashboard(manifest, d)


def test_the_dashboard_refuses_a_rejected_run(tmp_path):
    from huminloop.render import RenderError

    manifest = json.loads((FIXTURE / "manifest.json").read_text())
    d = tmp_path / manifest["run_id"]
    shutil.copytree(FIXTURE, d)
    manifest["status"] = "rejected"
    with pytest.raises(RenderError, match="rejected"):
        render_dashboard(manifest, d)


# ---------------------------------------------------------------------------
# The empty states. A thin run is the common case for a new engagement, and it was the one
# shape no test ever rendered.
# ---------------------------------------------------------------------------


def test_a_run_with_no_escalations_has_no_badge_and_says_so(minimal):
    assert '<span class="badge">' not in minimal
    assert "Nothing was escalated" in minimal
    assert "Nothing is blocking" in minimal


def test_a_run_with_no_challenges_says_so_rather_than_drawing_an_empty_debate(minimal):
    assert "No challenges were recorded" in minimal
    assert '<details class="pbrow' not in minimal


def test_a_run_with_no_context_invites_some_rather_than_showing_an_empty_chip_row(minimal):
    assert "No engagement context was supplied" in minimal
    assert '<span class="ctxchip' not in minimal


def test_an_errored_engagement_lead_degrades_the_plan_tab_instead_of_crashing(tmp_path):
    page = _render(ALL_RUNS["failed-synthesis"], tmp_path)
    assert "The Engagement Lead produced no plan." in page
    assert "No recommendation was produced." in page
    assert "No next steps were produced." in page


def test_the_rich_and_minimal_runs_disagree_about_everything_they_should(tmp_path):
    """The pair earns its keep only if the two actually take different branches."""
    rich = _render(ALL_RUNS["rich"], tmp_path / "a")
    thin = _render(ALL_RUNS["minimal"], tmp_path / "b")
    assert ('<span class="badge">' in rich) and ('<span class="badge">' not in thin)
    assert ("No challenges were recorded" in thin) and ("No challenges were recorded" not in rich)
    assert 'class="people bench"' in thin  # minimal carries staffing
    assert "Why each was called in" in rich  # rich predates it and still renders


def test_every_context_state_is_visually_distinct_from_read(tmp_path):
    """The chip class comes from state.split()[0]. A state with no matching CSS class renders
    identically to a file that was read fine — so a refused symlink would look normal."""
    import re as _re

    from huminloop.dashboard import _CSS

    manifest = json.loads((ALL_RUNS["minimal"] / "manifest.json").read_text())
    d = tmp_path / manifest["run_id"]
    shutil.copytree(ALL_RUNS["minimal"], d)
    manifest["context_read"] = [
        {"file": "ok.md", "chars": 10, "state": "read"},
        {"file": "cut.md", "chars": 5, "state": "truncated"},
        {"file": "dropped.md", "chars": 0, "state": "dropped (budget)"},
        {"file": "blank.md", "chars": 0, "state": "empty"},
        {"file": "locked.md", "chars": 0, "state": "unreadable (Permission denied)"},
        {"file": "gone.md", "chars": 0, "state": "unresolvable (No such file or directory)"},
        {
            "file": "sneaky.md",
            "chars": 0,
            "state": "refused (resolves outside the engagement)",
            "resolves_to": "/etc/passwd",
        },
    ]
    page = render_dashboard(manifest, d)

    styled = set(_re.findall(r"\.ctxchip\.([a-z]+)\{", _CSS))
    for row in manifest["context_read"]:
        word = row["state"].split()[0]
        if word == "read":
            continue
        assert word in styled, f"state {row['state']!r} has no .ctxchip.{word} rule"
        # And never colour alone — the word itself is on the chip (DESIGN.md).
        assert f"&middot; {word}" in page

    assert "/etc/passwd" in page  # where the refused link pointed, in the tooltip
    assert "&middot; read" not in page  # the ordinary case stays unlabelled
