"""The UI adds no rules. These tests exist to prove it cannot become a way around them."""

import json

import pytest

from huminloop import gate, orchestrator, server
from huminloop.cli import main
from huminloop.storage import artifact_root
from tests.test_cli import _STATES, _run_id_from


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


# The CLI's status contract, held to the web surface too: for every state, the page must render
# and must offer the one move `status` recommends, and posting that form must settle the run.
# Before this, an edited, interrupted or manifest-less run crashed or 404'd the page, so the web
# had no way to reject exactly the runs that most need rejecting.


@pytest.fixture
def live(state):
    import threading
    from http.server import ThreadingHTTPServer

    handler = type("TestHandler", (server.Handler,), {"state": state})
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield httpd.server_address[1]
    httpd.shutdown()
    httpd.server_close()


def _http(port, method, path, form=None):
    import http.client
    from urllib.parse import urlencode

    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    body = urlencode(form) if form else None
    headers = {"Content-Type": "application/x-www-form-urlencoded"} if form else {}
    conn.request(method, path, body=body, headers=headers)
    resp = conn.getresponse()
    return resp.status, resp.read().decode("utf-8")


def _offered(page, rid):
    import re

    return set(re.findall(rf'<form method="post" action="/run/{rid}/(\w+)">', page))


@pytest.mark.parametrize("name", list(_STATES))
def test_the_page_offers_and_accepts_the_move_status_recommends(
    workdir, capsys, failing_rename, state, live, name
):
    setup, expected = _STATES[name]
    assert main(["run", "Define KPIs and a dashboard"]) == 0
    rid = _run_id_from(capsys.readouterr().out)
    setup(rid, failing_rename)
    assert gate.status(rid)["pending_action"] == expected

    code, page = _http(live, "GET", f"/run/{rid}")
    assert code == 200 and "Traceback" not in page
    offered = _offered(page, rid)
    assert expected in offered
    if expected == "reject":
        assert "approve" not in offered  # never offer a move the gate will refuse

    form = {"token": state.token, "by": "Tony"}
    form |= {"reason": "failed verification"} if expected == "reject" else {"note": ""}
    code, body = _http(live, "POST", f"/run/{rid}/{expected}", form)
    assert code == 303, body
    assert gate.status(rid)["pending_action"] == "done"


def test_an_unrenderable_run_page_shows_why_and_not_the_content(workdir, capsys, state, live):
    assert main(["run", "Define KPIs and a dashboard"]) == 0
    rid = _run_id_from(capsys.readouterr().out)
    art = next((artifact_root() / "pending" / rid).glob("*.md"))
    art.write_text(art.read_text() + "\nSMUGGLED-IN-AFTER-THE-RUN\n")
    code, page = _http(live, "GET", f"/run/{rid}")
    assert code == 200
    assert "changed since the run" in page
    assert "SMUGGLED-IN-AFTER-THE-RUN" not in page  # a page that shows content vouches for it


def test_a_rejected_run_page_renders(workdir, capsys, state, live):
    assert main(["run", "Define KPIs and a dashboard"]) == 0
    rid = _run_id_from(capsys.readouterr().out)
    assert main(["reject", rid, "--by", "Tony", "--reason", "no"]) == 0
    code, page = _http(live, "GET", f"/run/{rid}")
    assert code == 200 and "reopen" in _offered(page, rid)


def test_a_move_the_web_cannot_make_names_the_command_that_can(
    workdir, capsys, monkeypatch, state, live
):
    """An interrupted run whose lead failed: `status` says resynthesize, which has no form."""
    import huminloop.cli as cli
    from tests.conftest import RecordingLLM

    monkeypatch.setattr(
        cli, "get_llm", lambda provider=None: RecordingLLM(fail_roles=("engagement_lead",))
    )
    assert main(["run", "Draft an RFP response and SOW"]) == 0
    rid = _run_id_from(capsys.readouterr().out)
    mf = artifact_root() / "pending" / rid / "manifest.json"
    mf.write_text(json.dumps(json.loads(mf.read_text()) | {"status": "running"}))
    assert gate.status(rid)["pending_action"] == "resynthesize"

    code, page = _http(live, "GET", f"/run/{rid}")
    assert code == 200
    assert f"huminloop resynthesize {rid}" in page
    assert _offered(page, rid) == set()


def _set_manifest(rid, **fields):
    mf = artifact_root() / "pending" / rid / "manifest.json"
    mf.write_text(json.dumps(json.loads(mf.read_text()) | fields))


def test_the_fallback_escapes_every_manifest_field_it_prints(workdir, capsys, state, live):
    """The manifest is attacker-editable; the reason the page prints comes from it."""
    assert main(["run", "Define KPIs and a dashboard"]) == 0
    rid = _run_id_from(capsys.readouterr().out)
    _set_manifest(rid, status="<script>alert(1)</script>")
    code, page = _http(live, "GET", f"/run/{rid}")
    assert code == 200 and "<script>alert(1)</script>" not in page
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in page
    code, page = _http(live, "POST", f"/run/{rid}/reject", {"token": "bad"})
    assert "<script>alert(1)</script>" not in page and "Stale or missing form token" in page

    # A gate error on POST quotes the manifest too, and comes back through the error banner.
    mf = artifact_root() / "pending" / rid / "manifest.json"
    m = json.loads(mf.read_text())
    next(a for a in m["artifacts"] if a.get("file"))["file"] = "<img src=x onerror=alert(2)>.md"
    mf.write_text(json.dumps(m))
    form = {"token": state.token, "by": "Tony", "note": ""}
    code, page = _http(live, "POST", f"/run/{rid}/approve", form)
    assert "<img src=x" not in page and "&lt;img src=x" in page  # the error banner


def test_an_unrenderable_run_the_gate_would_approve_names_the_command(workdir, capsys, state, live):
    """It printed the bare word "approve": no form, no command, no way forward."""
    assert main(["run", "Define KPIs and a dashboard"]) == 0
    rid = _run_id_from(capsys.readouterr().out)
    _set_manifest(rid, status="complete")
    assert gate.status(rid)["pending_action"] == "approve"
    code, page = _http(live, "GET", f"/run/{rid}")
    assert code == 200 and _offered(page, rid) == set()
    assert f"huminloop approve {rid}" in page and f"huminloop show {rid}" in page


def test_a_manifest_the_renderer_chokes_on_still_gets_a_page(workdir, capsys, state, live):
    """A `plan` that is a string raised AttributeError and dropped the connection."""
    assert main(["run", "Define KPIs and a dashboard"]) == 0
    rid = _run_id_from(capsys.readouterr().out)
    _set_manifest(rid, plan="x")
    code, page = _http(live, "GET", f"/run/{rid}")
    assert code == 200 and "could not be built" in page and "Traceback" not in page


def test_a_live_run_page_says_to_wait(workdir, capsys, state, live):
    from huminloop.storage import write_lock

    assert main(["run", "Define KPIs and a dashboard"]) == 0
    rid = _run_id_from(capsys.readouterr().out)
    _set_manifest(rid, status="running")
    write_lock(artifact_root() / "pending" / rid)  # this process is alive
    assert gate.status(rid)["pending_action"] == "wait"
    code, page = _http(live, "GET", f"/run/{rid}")
    assert "still being written" in page and _offered(page, rid) == set()


def test_the_fallback_says_why_truthfully(workdir, capsys, failing_rename, state, live):
    """It told every refused run its contents failed verification, whatever the reason."""
    assert main(["run", "Define KPIs and a dashboard"]) == 0
    rid = _run_id_from(capsys.readouterr().out)
    _set_manifest(rid, status="running")
    assert gate.status(rid)["artifacts_verified"] is True
    _, page = _http(live, "GET", f"/run/{rid}")
    assert "did not finish" in page and "cannot be verified" not in page

    assert main(["run", "Define KPIs and a dashboard"]) == 0
    rid = _run_id_from(capsys.readouterr().out)
    brk, restore = failing_rename
    brk()
    with pytest.raises(OSError):
        gate.reject(rid, by="Tony", reason="first look")
    restore()
    _, page = _http(live, "GET", f"/run/{rid}")
    assert "A reject by Tony is already recorded" in page and "original reason" in page


def test_the_fallback_escapes_the_name_on_a_recorded_reject(
    workdir, capsys, failing_rename, state, live
):
    """The recorded decider's name comes from the manifest and is printed on the page."""
    assert main(["run", "Define KPIs and a dashboard"]) == 0
    rid = _run_id_from(capsys.readouterr().out)
    brk, restore = failing_rename
    brk()
    with pytest.raises(OSError):
        gate.reject(rid, by="<b>Tony</b>", reason="first look")
    restore()
    art = next((artifact_root() / "pending" / rid).glob("*.md"))
    art.write_text(art.read_text() + "\nedited\n")  # the renderer refuses; the fallback prints
    code, page = _http(live, "GET", f"/run/{rid}")
    assert code == 200 and "A reject by &lt;b&gt;Tony&lt;/b&gt; is already recorded" in page
    assert "<b>Tony</b>" not in page


def test_a_non_string_flag_does_not_take_down_the_inbox(workdir, capsys, state, live):
    """One `process_flags: [5]` crashed the list page for every run."""
    assert main(["run", "Define KPIs and a dashboard"]) == 0
    rid = _run_id_from(capsys.readouterr().out)
    mf = artifact_root() / "pending" / rid / "manifest.json"
    m = json.loads(mf.read_text())
    m["artifacts"][0]["process_flags"] = [5]
    mf.write_text(json.dumps(m))
    code, page = _http(live, "GET", "/")
    assert code == 200 and rid in page
    code, page = _http(live, "GET", f"/run/{rid}")
    assert code == 200 and "reject" in _offered(page, rid)


def test_a_non_string_recorded_name_still_gets_a_page(workdir, capsys, failing_rename, state, live):
    assert main(["run", "Define KPIs and a dashboard"]) == 0
    rid = _run_id_from(capsys.readouterr().out)
    brk, restore = failing_rename
    brk()
    with pytest.raises(OSError):
        gate.reject(rid, by="Tony", reason="first look")
    restore()
    _set_manifest(
        rid,
        decision=json.loads((artifact_root() / "pending" / rid / "manifest.json").read_text())[
            "decision"
        ]
        | {"by": 5},
    )
    code, page = _http(live, "GET", f"/run/{rid}")
    assert code == 200 and "reject" in _offered(page, rid)


def test_a_malformed_decision_still_gets_a_reject_form(workdir, capsys, state, live):
    assert main(["run", "Define KPIs and a dashboard"]) == 0
    rid = _run_id_from(capsys.readouterr().out)
    _set_manifest(rid, decision="approved")
    code, page = _http(live, "GET", f"/run/{rid}")
    assert code == 200 and _offered(page, rid) == {"reject"}
    form = {"token": state.token, "by": "Tony", "reason": "malformed"}
    assert _http(live, "POST", f"/run/{rid}/reject", form)[0] == 303


def test_an_edited_run_is_told_it_failed_verification(workdir, capsys, state, live):
    """The most common refused run had no test pinning its explanation."""
    assert main(["run", "Define KPIs and a dashboard"]) == 0
    rid = _run_id_from(capsys.readouterr().out)
    art = next((artifact_root() / "pending" / rid).glob("*.md"))
    art.write_text(art.read_text() + "\nedited\n")
    _, page = _http(live, "GET", f"/run/{rid}")
    assert "cannot be verified" in page and "did not finish" not in page


@pytest.mark.parametrize(
    "fields",
    [{"decisions": ["x"]}, {"decisions": "x"}, {"annotations": 5}],
    ids=["history-entry", "history-string", "annotations-number"],
)
def test_edited_history_on_one_run_does_not_take_down_the_inbox(
    workdir, capsys, state, live, fields
):
    assert main(["run", "Define KPIs and a dashboard"]) == 0
    rid = _run_id_from(capsys.readouterr().out)
    _set_manifest(rid, **fields)
    code, page = _http(live, "GET", "/")
    assert code == 200 and rid in page


def test_the_verdict_is_escaped():
    """`decision.state` reached the page raw, beside the POST token: one edit ran script."""
    from huminloop.render import _decision_bar

    bar = _decision_bar({"status": "approved", "decision": {"state": "<img src=x onerror=1>"}})
    assert "<IMG" not in bar and "&LT;IMG" in bar.upper()


def test_an_edited_verdict_never_renders(workdir, capsys, state, live, failing_rename):
    assert main(["run", "Define KPIs and a dashboard"]) == 0
    rid = _run_id_from(capsys.readouterr().out)
    gate.approve(rid, by="Tony")
    mf = artifact_root() / "approved" / rid / "manifest.json"
    m = json.loads(mf.read_text())
    m["decision"]["state"] = "<img src=x onerror=1>"
    mf.write_text(json.dumps(m))
    code, page = _http(live, "GET", f"/run/{rid}")
    assert code == 200 and "<img src=x" not in page.lower()
    assert "malformed" in page and "reopen" in _offered(page, rid)


def test_a_scalar_process_flags_is_still_shown():
    m = {"artifacts": [{"role": "r", "process_flags": "Escalated to the human: budget"}]}
    assert server.escalations(m) == ["budget"]
    assert server.other_flags({"artifacts": [{"role": "r", "process_flags": 5}]}) == ["r: 5"]


def test_the_fallback_logs_the_render_failure(workdir, capsys, state, live, caplog):
    """The broad fallback would otherwise hide a real renderer bug without a trace."""
    assert main(["run", "Define KPIs and a dashboard"]) == 0
    rid = _run_id_from(capsys.readouterr().out)
    _set_manifest(rid, plan="not a plan")
    with caplog.at_level("ERROR", logger="huminloop.server"):
        _http(live, "GET", f"/run/{rid}")
    assert any(rid in r.getMessage() and r.exc_info for r in caplog.records)


def test_a_flag_field_that_is_a_bare_string_shows_whole():
    """Without the list check a string was iterated character by character."""
    m = {"artifacts": [{"role": "analyst", "process_flags": "odd"}]}
    assert server.other_flags(m) == ["analyst: odd"]
