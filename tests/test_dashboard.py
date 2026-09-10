"""The dashboard is a working surface, not a document. These pin the parts you scan."""

import json
import shutil
from pathlib import Path

import pytest

from huminloop.dashboard import TABS, _bar, _donut, _is_client_step, _steps, render_dashboard

FIXTURE = Path(__file__).resolve().parents[1] / "docs" / "example-run" / "enablement"


@pytest.fixture
def page(tmp_path):
    manifest = json.loads((FIXTURE / "manifest.json").read_text())
    d = tmp_path / manifest["run_id"]
    shutil.copytree(FIXTURE, d)
    return render_dashboard(manifest, d)


def test_every_tab_has_a_pane(page):
    for tid, label in TABS:
        assert f'data-t="{tid}"' in page and f'id="p-{tid}"' in page
        assert label in page


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
