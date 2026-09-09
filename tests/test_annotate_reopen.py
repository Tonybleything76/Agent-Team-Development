import json

import pytest

from huminloop import gate, orchestrator, stats
from huminloop.cli import main
from huminloop.storage import artifact_root, log_path


def _run(llm, task="Define KPIs"):
    return orchestrator.run(task, llm=llm, critique=False)


def test_annotate_records_a_note_without_changing_status(workdir, fake_llm):
    rec = _run(fake_llm)
    m = gate.annotate(rec.run_id, by="Tony", note="the ROI section assumes a baseline we lack")
    assert m["status"] == "pending"
    assert m["annotations"][0]["by"] == "Tony"
    assert "baseline" in m["annotations"][0]["note"]
    assert m["annotations"][0]["state_when_written"] == "pending"
    assert gate.find_run(artifact_root(), rec.run_id)[0] == "pending"


def test_annotations_are_append_only_and_work_after_a_decision(workdir, fake_llm):
    rec = _run(fake_llm)
    gate.annotate(rec.run_id, by="Tony", note="first thought")
    gate.approve(rec.run_id, by="Tony")
    m = gate.annotate(rec.run_id, by="Tony", note="second thought, after approving")
    assert [a["note"] for a in m["annotations"]] == [
        "first thought",
        "second thought, after approving",
    ]
    assert m["annotations"][1]["state_when_written"] == "approved"
    assert m["status"] == "approved"


def test_annotate_requires_a_name_and_something_to_say(workdir, fake_llm):
    rec = _run(fake_llm)
    with pytest.raises(gate.GateError, match="named author"):
        gate.annotate(rec.run_id, by="  ", note="x")
    with pytest.raises(gate.GateError, match="something to say"):
        gate.annotate(rec.run_id, by="Tony", note="   ")


def test_reopen_supersedes_a_decision_without_erasing_it(workdir, fake_llm):
    rec = _run(fake_llm)
    gate.approve(rec.run_id, by="Tony", note="looked fine at the time")
    m = gate.reopen(rec.run_id, by="Tony", reason="the benchmark turned out to be wrong")
    assert m["status"] == "pending" and m["decision"] is None
    # The superseded approval is still in the history.
    assert [d["state"] for d in m["decisions"]] == ["approved", "reopened"]
    assert (
        m["decisions"][0]["by"] == "Tony" and m["decisions"][0]["note"] == "looked fine at the time"
    )
    assert m["decisions"][1]["supersedes"]["state"] == "approved"
    assert gate.find_run(artifact_root(), rec.run_id)[0] == "pending"


def test_a_reopened_run_can_be_decided_again(workdir, fake_llm):
    rec = _run(fake_llm)
    gate.approve(rec.run_id, by="Tony")
    gate.reopen(rec.run_id, by="Tony", reason="changed my mind")
    m = gate.reject(rec.run_id, by="Tony", reason="the assumption does not hold")
    assert m["status"] == "rejected"
    assert [d["state"] for d in m["decisions"]] == ["approved", "reopened", "rejected"]
    assert gate.find_run(artifact_root(), rec.run_id)[0] == "rejected"


def test_reopen_needs_a_reason_and_a_decision_to_reopen(workdir, fake_llm):
    rec = _run(fake_llm)
    with pytest.raises(gate.GateError, match="already pending"):
        gate.reopen(rec.run_id, by="Tony", reason="x")
    gate.approve(rec.run_id, by="Tony")
    with pytest.raises(gate.GateError, match="reason is required"):
        gate.reopen(rec.run_id, by="Tony", reason="  ")


def test_reopen_and_annotate_are_logged(workdir, fake_llm):
    rec = _run(fake_llm)
    gate.annotate(rec.run_id, by="Tony", note="a reservation")
    gate.approve(rec.run_id, by="Tony")
    gate.reopen(rec.run_id, by="Tony", reason="second thoughts")
    events = [json.loads(line) for line in log_path().read_text().splitlines()]
    kinds = [e["event"] for e in events]
    assert "annotated" in kinds and "reopened" in kinds
    reopened = next(e for e in events if e["event"] == "reopened")
    assert reopened["supersedes"]["by"] == "Tony" and reopened["note"] == "second thoughts"


def test_cli_annotate_reopen_and_stats(workdir, fake_llm, capsys, monkeypatch):
    import huminloop.cli as cli

    monkeypatch.setattr(cli, "get_llm", lambda provider=None: fake_llm)
    assert main(["run", "Define KPIs", "--no-critique"]) == 0
    run_id = capsys.readouterr().out.split("run_id: ")[1].split()[0]

    assert main(["annotate", run_id, "--by", "Tony", "--note", "unsure about phase 2"]) == 0
    assert "status unchanged" in capsys.readouterr().out
    assert main(["approve", run_id, "--by", "Tony"]) == 0
    capsys.readouterr()
    assert main(["reopen", run_id, "--by", "Tony", "--reason", "benchmark was wrong"]) == 0
    assert "superseded approved by Tony" in capsys.readouterr().out

    assert main(["stats"]) == 0
    out = capsys.readouterr().out
    assert "annotations" in out and "reopened" in out


def test_stats_flags_total_agreement_as_worth_a_look():
    summary = stats.summarize(
        [{"event": "critique", "points": 6, "accepted": 6, "revised": True}] * 2
    )
    assert summary["critique_acceptance_rate"] == 1.0
    assert any("half its job" in w for w in stats.warnings(summary))


def test_stats_says_nothing_when_the_sample_is_too_small():
    summary = stats.summarize([{"event": "critique", "points": 2, "accepted": 2}])
    assert summary["critique_acceptance_rate"] == 1.0
    assert not any("half its job" in w for w in stats.warnings(summary))


def test_stats_survives_a_corrupt_log_line(workdir, tmp_path):
    p = tmp_path / "runs.jsonl"
    p.write_text('{"event": "run_start"}\n{ this is not json\n{"event": "run_end"}\n')
    assert stats.summarize(stats.read_events(p))["runs_completed"] == 1


def test_show_and_pending_surface_notes_and_reopens(workdir, fake_llm, capsys, monkeypatch):
    import huminloop.cli as cli

    monkeypatch.setattr(cli, "get_llm", lambda provider=None: fake_llm)
    assert main(["run", "Define KPIs", "--no-critique"]) == 0
    run_id = capsys.readouterr().out.split("run_id: ")[1].split()[0]
    gate.annotate(run_id, by="Tony", note="phase 2 needs a baseline")
    gate.approve(run_id, by="Tony")
    gate.reopen(run_id, by="Tony", reason="the baseline never arrived")

    assert main(["pending"]) == 0
    listing = capsys.readouterr().out
    assert "1 note(s)" in listing and "reopened x1" in listing

    assert main(["show", run_id]) == 0
    shown = capsys.readouterr().out
    assert "[reopened] by Tony" in shown and "supersedes approved by Tony" in shown
    assert "[note] Tony" in shown and "phase 2 needs a baseline" in shown


def test_annotation_text_cannot_repaint_the_terminal(workdir, fake_llm, capsys):
    rec = _run(fake_llm)
    gate.annotate(rec.run_id, by="Tony", note="clean\x1b[2J\x1b[Hnow APPROVED")
    assert main(["show", rec.run_id]) == 0
    shown = capsys.readouterr().out
    assert "\x1b" not in shown and "now APPROVED" in shown
