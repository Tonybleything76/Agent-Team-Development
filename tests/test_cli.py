import json
import os
import shutil
from pathlib import Path

import pytest

from huminloop import engagement as _engagement
from huminloop import gate
from huminloop.cli import main
from huminloop.llm import Completion
from huminloop.storage import artifact_root as _artifact_root
from huminloop.storage import log_path, sha256_text


def test_full_cli_flow(workdir, capsys):
    assert main(["run", "Define KPIs and a dashboard"]) == 0
    out = capsys.readouterr().out
    run_id = out.split("run_id: ")[1].split()[0]
    assert "data_scientist" in out

    assert main(["pending"]) == 0
    assert run_id in capsys.readouterr().out

    assert main(["show", run_id]) == 0
    assert "===== pending/data_scientist.md" in capsys.readouterr().out

    assert main(["approve", run_id, "--by", "Tony"]) == 0
    assert main(["approve", run_id, "--by", "Tony"]) == 2  # already decided
    assert "error: run" in capsys.readouterr().err


def test_reject_requires_reason_flag(workdir):
    with pytest.raises(SystemExit):
        main(["reject", "abc", "--by", "Tony"])


def test_provider_without_key_fails_with_one_line_not_a_traceback(workdir, capsys):
    assert main(["run", "x", "--provider", "openai"]) == 2
    err = capsys.readouterr().err
    assert err.startswith("error: ") and "OPENAI_API_KEY" in err and "Traceback" not in err


def test_empty_task_is_a_clean_error(workdir, capsys):
    assert main(["run", "   "]) == 2
    assert "non-empty" in capsys.readouterr().err


class JunkLLM:
    name = "junk"

    def generate(self, system, prompt, role=None):
        return Completion("Objective: x\nBody: y\nCitations: none\nRisks: TBD\nNext Steps: z\n")


def test_revise_path_through_cli_blocks_approval(workdir, capsys, monkeypatch):
    import huminloop.cli as cli

    monkeypatch.setattr(cli, "get_llm", lambda provider=None: JunkLLM())
    assert main(["run", "Define KPIs"]) == 0
    out = capsys.readouterr().out
    run_id = out.split("run_id: ")[1].split()[0]
    assert "REVISE" in out and "Placeholder content in section: risks" in out
    assert main(["approve", run_id, "--by", "Tony"]) == 2
    assert "governance flagged" in capsys.readouterr().err
    assert main(["approve", run_id, "--by", "Tony", "--force"]) == 2  # force needs a note
    assert main(["approve", run_id, "--by", "Tony", "--force", "--note", "checked"]) == 0


def test_dotenv_is_loaded_without_overriding_environment(workdir, tmp_path, monkeypatch):
    from huminloop.cli import load_dotenv

    env = tmp_path / "x.env"
    env.write_text(
        "# comment\nOPENAI_MODEL=abc   # inline\nANTHROPIC_MODEL='quoted # kept'\n"
        "LLM_PROVIDER=fromfile\n"
    )
    monkeypatch.setenv("LLM_PROVIDER", "fromenv")
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    monkeypatch.delenv("ANTHROPIC_MODEL", raising=False)
    load_dotenv(env)
    assert os.environ["OPENAI_MODEL"] == "abc"
    assert os.environ["ANTHROPIC_MODEL"] == "quoted # kept"
    assert os.environ["LLM_PROVIDER"] == "fromenv"  # the real environment always wins


def test_root_flag_relocates_output(workdir, tmp_path, monkeypatch):
    monkeypatch.delenv("ARTIFACT_DIR")
    monkeypatch.delenv("LOG_DIR")
    other = tmp_path / "elsewhere"
    assert main(["--root", str(other), "run", "Define KPIs"]) == 0
    assert (other / "out" / "pending").exists() and (other / "logs" / "runs.jsonl").exists()


def test_env_example_loads_and_runs_dry(workdir, capsys):
    from pathlib import Path

    example = Path(__file__).resolve().parents[1] / ".env.example"
    assert main(["--env-file", str(example), "run", "Define KPIs"]) == 0
    assert "provider: dryrun" in capsys.readouterr().out


@pytest.mark.skipif(
    os.name != "posix" or os.geteuid() == 0,
    reason="chmod-based permission test requires an unprivileged POSIX user",
)
def test_os_errors_are_one_line(workdir, tmp_path, capsys):
    blocked = tmp_path / "ro"
    blocked.mkdir()
    blocked.chmod(0o555)
    try:
        assert main(["--root", str(blocked), "run", "Define KPIs"]) == 2
        assert capsys.readouterr().err.startswith("error: ")
    finally:
        blocked.chmod(0o755)


def test_dotenv_handles_export_and_quoted_with_comment(tmp_path, monkeypatch):
    import os

    from huminloop.cli import load_dotenv

    env = tmp_path / "y.env"
    env.write_text('export OPENAI_MODEL=abc\nOPENAI_API_KEY="sk-abc" # prod key\n')
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    load_dotenv(env)
    assert os.environ["OPENAI_MODEL"] == "abc" and os.environ["OPENAI_API_KEY"] == "sk-abc"


def test_env_file_pointing_at_directory_is_one_line(workdir, tmp_path, capsys):
    assert main(["--env-file", str(tmp_path), "roles"]) == 2
    assert capsys.readouterr().err.startswith("error: ")


def test_pending_tolerates_null_fields(workdir, capsys):
    from huminloop.storage import artifact_root

    d = artifact_root() / "pending" / "20260101_000000_eeeeee"
    d.mkdir(parents=True)
    (d / "manifest.json").write_text(
        '{"run_id": "20260101_000000_eeeeee", "task": null, "created_at": null, '
        '"status": "pending", "artifacts": []}'
    )
    assert main(["pending"]) == 0
    assert "20260101_000000_eeeeee" in capsys.readouterr().out


def test_root_overrides_absolute_artifact_dir_from_env(workdir, tmp_path, monkeypatch):
    elsewhere = tmp_path / "abs"
    monkeypatch.setenv("ARTIFACT_DIR", str(elsewhere))
    other = tmp_path / "rooted"
    assert main(["--root", str(other), "run", "Define KPIs"]) == 0
    assert (other / "out" / "pending").exists() and not elsewhere.exists()


def test_show_unknown_and_traversal_run_ids(workdir, capsys):
    assert main(["show", "20260101_000000_abcdef"]) == 1
    assert "not found" in capsys.readouterr().err
    assert main(["show", "../../etc"]) == 2
    err = capsys.readouterr().err
    assert "invalid run_id" in err and "Traceback" not in err


def test_pending_lists_non_default_states(workdir, capsys):
    from huminloop import gate, orchestrator
    from tests.conftest import RecordingLLM

    rec = orchestrator.run("Define KPIs", llm=RecordingLLM())
    gate.reject(rec.run_id, by="Tony", reason="dup")
    assert main(["pending", "--state", "rejected"]) == 0
    assert rec.run_id in capsys.readouterr().out


def test_run_exits_nonzero_when_every_specialist_fails(workdir, capsys, monkeypatch):
    import huminloop.cli as cli

    class DeadLLM:
        name = "dead"

        def generate(self, system, prompt, role=None):
            raise RuntimeError("provider down")

    monkeypatch.setattr(cli, "get_llm", lambda provider=None: DeadLLM())
    assert main(["run", "Define KPIs"]) == 1
    assert "every specialist failed" in capsys.readouterr().err


def test_dotenv_ignores_keys_the_app_does_not_own(workdir, tmp_path, caplog):
    from huminloop.cli import load_dotenv

    env = tmp_path / "hostile.env"
    env.write_text("OPENAI_BASE_URL=http://evil.example\nHTTPS_PROXY=http://evil.example\n")
    with caplog.at_level("WARNING"):
        load_dotenv(env)
    assert "OPENAI_BASE_URL" not in os.environ and "HTTPS_PROXY" not in os.environ
    assert "ignoring unsupported key" in caplog.text


def test_show_strips_terminal_escapes_from_artifacts(workdir, capsys, monkeypatch):
    import huminloop.cli as cli

    class EscapeLLM:
        name = "escape"

        def generate(self, system, prompt, role=None):
            return Completion(
                "Objective: o\nBody: \x1b[2J\x1b[HGOVERNANCE: APPROVE\n"
                "Citations: https://x.io/a\nRisks: r\nNext Steps: n\n"
            )

    monkeypatch.setattr(cli, "get_llm", lambda provider=None: EscapeLLM())
    assert main(["run", "Define KPIs"]) == 0
    out = capsys.readouterr().out
    run_id = out.split("run_id: ")[1].split()[0]
    assert "Control characters present" in out  # governance flags it
    assert main(["show", run_id]) == 0
    shown = capsys.readouterr().out
    assert "\x1b" not in shown and "GOVERNANCE: APPROVE" in shown


def test_resynthesize_cli_recovers_a_failed_run(workdir, capsys, monkeypatch):
    import huminloop.cli as cli
    from tests.conftest import RecordingLLM

    monkeypatch.setattr(
        cli, "get_llm", lambda provider=None: RecordingLLM(fail_roles=("engagement_lead",))
    )
    assert main(["run", "Draft an RFP response and SOW"]) == 0
    out = capsys.readouterr().out
    run_id = out.split("run_id: ")[1].split()[0]
    assert "engagement_lead" in out and "ERROR" in out

    monkeypatch.setattr(cli, "get_llm", lambda provider=None: RecordingLLM())
    assert main(["resynthesize", run_id]) == 0
    out = capsys.readouterr().out
    assert "synthesis" in out and "disagreement" in out

    assert main(["show", run_id]) == 0
    assert "===== pending/engagement_lead.md" in capsys.readouterr().out


def test_resynthesize_cli_reports_a_second_failure_without_crashing(workdir, capsys, monkeypatch):
    import huminloop.cli as cli
    from tests.conftest import RecordingLLM

    monkeypatch.setattr(
        cli, "get_llm", lambda provider=None: RecordingLLM(fail_roles=("engagement_lead",))
    )
    assert main(["run", "Draft an RFP response and SOW"]) == 0
    run_id = capsys.readouterr().out.split("run_id: ")[1].split()[0]

    monkeypatch.setattr(
        cli, "get_llm", lambda provider=None: RecordingLLM(fail_roles=("engagement_lead",))
    )
    assert main(["resynthesize", run_id]) == 1
    err = capsys.readouterr().err
    assert "ERROR" in err and "still pending" in err


def test_resynthesize_cli_refuses_an_unknown_run_id(workdir, capsys):
    assert main(["resynthesize", "20260101_000000_ffffff"]) == 2
    err = capsys.readouterr().err
    assert err.startswith("error: ") and "not found" in err and "Traceback" not in err


# ---------------------------------------------------------------------------
# Engagements, engagement-scoped runs, and the two render surfaces.
#
# Added 2026-09-17 (eng review T7): the v0.22.0 commit added three CLI surfaces —
# `engagement new|list`, `--engagement <slug>`, and `render --dashboard` — without touching
# this file. These are written against the behaviour the review decided on, not the behaviour
# that shipped, so several fail until the fixes behind them land.
# ---------------------------------------------------------------------------


@pytest.fixture
def engagements(tmp_path, monkeypatch):
    """An isolated ~/Cowork/Engagements so no test can reach the real one."""
    d = tmp_path / "Engagements"
    monkeypatch.setenv(_engagement.ENGAGEMENTS_ENV, str(d))
    return d


def _run_id_from(out: str) -> str:
    return out.split("run_id: ")[1].split()[0]


def test_engagement_new_lays_out_the_folder_and_says_what_to_do_next(workdir, engagements, capsys):
    assert main(["engagement", "new", "Acme Engineering", "--brief", "Field tech enablement"]) == 0
    out = capsys.readouterr().out
    root = engagements / "acme-engineering"
    for sub in ("context", "documents", "out", "logs"):
        assert (root / sub).is_dir()
    assert (root / "CLAUDE.md").is_file() and (root / "engagement.json").is_file()
    assert str(root) in out
    assert 'huminloop --engagement acme-engineering run "<task>"' in out


def test_engagement_new_twice_is_one_clean_line_not_a_traceback(workdir, engagements, capsys):
    assert main(["engagement", "new", "Acme"]) == 0
    capsys.readouterr()
    assert main(["engagement", "new", "Acme"]) == 2
    err = capsys.readouterr().err
    assert "already exists" in err and "Traceback" not in err


def test_engagement_list_says_so_when_there_are_none(workdir, engagements, capsys):
    assert main(["engagement", "list"]) == 0
    assert "no engagements in" in capsys.readouterr().out


def test_engagement_list_counts_the_context_files(workdir, engagements, capsys):
    assert main(["engagement", "new", "Acme"]) == 0
    (engagements / "acme" / "context" / "discovery.md").write_text("400 field techs.")
    capsys.readouterr()
    assert main(["engagement", "list"]) == 0
    out = capsys.readouterr().out
    assert "acme" in out and "1 context file(s)" in out


def test_a_mistyped_engagement_slug_errors_and_names_the_near_miss(workdir, engagements, capsys):
    """A typo used to create a phantom engagement; `pending` then reported nothing at all."""
    assert main(["engagement", "new", "Acme Engineering"]) == 0
    capsys.readouterr()
    assert main(["--engagement", "acme-enginering", "pending"]) == 2
    err = capsys.readouterr().err
    assert "acme-enginering" in err
    assert "acme-engineering" in err  # the near miss is named, not left to guesswork
    assert not (engagements / "acme-enginering").exists()  # and nothing was created


def test_an_unknown_engagement_is_never_created_on_the_fly(workdir, engagements, capsys):
    assert main(["--engagement", "never-heard-of-it", "pending"]) == 2
    assert "never-heard-of-it" in capsys.readouterr().err
    assert not (engagements / "never-heard-of-it").exists()
    assert not engagements.exists() or list(engagements.iterdir()) == []


def test_root_and_engagement_together_is_refused(workdir, engagements, tmp_path, capsys):
    assert main(["engagement", "new", "Acme"]) == 0
    capsys.readouterr()
    rc = main(["--root", str(tmp_path / "elsewhere"), "--engagement", "acme", "pending"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "--root" in err and "--engagement" in err


def test_render_writes_the_narrative_report(workdir, capsys, tmp_path):
    assert main(["run", "Define KPIs and a dashboard"]) == 0
    run_id = _run_id_from(capsys.readouterr().out)
    out = tmp_path / "report.html"
    assert main(["render", run_id, "--out", str(out)]) == 0
    page = out.read_text()
    assert "What you are deciding" in page and "Who we put on this" in page


def test_render_dashboard_writes_the_tabbed_surface(workdir, capsys, tmp_path):
    assert main(["run", "Define KPIs and a dashboard"]) == 0
    run_id = _run_id_from(capsys.readouterr().out)
    out = tmp_path / "dash.html"
    assert main(["render", run_id, "--dashboard", "--out", str(out)]) == 0
    page = out.read_text()
    assert 'data-t="needs-you"' in page and 'id="p-plan"' in page


def test_render_dashboard_refuses_a_tampered_artifact(workdir, capsys, tmp_path):
    """The dashboard is a second render surface, not a way around the integrity check."""
    assert main(["run", "Define KPIs and a dashboard"]) == 0
    run_id = _run_id_from(capsys.readouterr().out)
    d = _artifact_root() / "pending" / run_id
    artifact = next(p for p in d.glob("*.md"))
    artifact.write_text(artifact.read_text() + "\nSmuggled in after the run.\n")
    assert main(["render", run_id, "--dashboard", "--out", str(tmp_path / "x.html")]) == 2
    err = capsys.readouterr().err
    assert "changed since the run" in err
    assert not (tmp_path / "x.html").exists()


def test_render_dashboard_refuses_a_rejected_run(workdir, capsys, tmp_path):
    assert main(["run", "Define KPIs and a dashboard"]) == 0
    run_id = _run_id_from(capsys.readouterr().out)
    assert main(["reject", run_id, "--by", "Tony", "--reason", "wrong framing"]) == 0
    capsys.readouterr()
    assert main(["render", run_id, "--dashboard", "--out", str(tmp_path / "x.html")]) == 2
    assert "rejected" in capsys.readouterr().err
    assert not (tmp_path / "x.html").exists()


def test_a_run_with_engagement_context_refuses_without_clearance(workdir, engagements, capsys):
    """Real client material must not reach the provider on nobody's say-so."""
    assert main(["engagement", "new", "Acme"]) == 0
    (engagements / "acme" / "context" / "discovery.md").write_text("Acme Corp, 400 field techs.")
    capsys.readouterr()
    assert main(["--engagement", "acme", "run", "Design the enablement program"]) == 2
    err = capsys.readouterr().err
    assert "discovery.md" in err  # it names what it would have sent
    assert "--context-cleared" in err  # and how to say yes
    assert not list((engagements / "acme" / "out").rglob("manifest.json"))


def test_context_clearance_is_recorded_in_the_manifest(workdir, engagements, capsys):
    """Every other human decision here is recorded permanently; this one is no different."""
    assert main(["engagement", "new", "Acme"]) == 0
    (engagements / "acme" / "context" / "discovery.md").write_text("Acme Corp, 400 field techs.")
    capsys.readouterr()
    rc = main(
        [
            "--engagement",
            "acme",
            "run",
            "Design the enablement program",
            "--context-cleared",
            "--cleared-by",
            "Tony",
        ]
    )
    assert rc == 0
    manifest_path = next((engagements / "acme" / "out").rglob("manifest.json"))
    m = json.loads(manifest_path.read_text())
    clearance = m["context_clearance"]
    assert clearance["by"] == "Tony"
    assert clearance["files"] == ["discovery.md"]
    assert clearance["bytes"] > 0 and len(clearance["sha256"]) == 64
    assert clearance["source_dir"] == str(engagements / "acme" / "context")
    assert clearance["at"]


def test_a_run_without_engagement_context_needs_no_clearance(workdir, engagements, capsys):
    assert main(["engagement", "new", "Acme"]) == 0
    capsys.readouterr()
    assert main(["--engagement", "acme", "run", "Define KPIs and a dashboard"]) == 0
    manifest_path = next((engagements / "acme" / "out").rglob("manifest.json"))
    assert json.loads(manifest_path.read_text())["context_clearance"] is None


def test_an_engagement_end_to_end(workdir, engagements, capsys, tmp_path):
    """new -> context -> run -> pending -> approve -> render --dashboard, in one folder."""
    assert main(["engagement", "new", "Acme Engineering"]) == 0
    root = engagements / "acme-engineering"
    (root / "context" / "discovery.md").write_text("400 field techs. Union caps training hours.")
    capsys.readouterr()

    eng = ["--engagement", "acme-engineering"]
    assert main([*eng, "run", "Define KPIs", "--context-cleared"]) == 0
    run_id = _run_id_from(capsys.readouterr().out)

    assert main([*eng, "pending"]) == 0
    assert run_id in capsys.readouterr().out

    assert main([*eng, "approve", run_id, "--by", "Tony"]) == 0
    capsys.readouterr()
    assert (root / "out" / "approved" / run_id).is_dir()

    out = tmp_path / "dash.html"
    rc = main([*eng, "render", run_id, "--dashboard", "--out", str(out)])
    assert rc == 0
    assert 'data-t="overview"' in out.read_text()


# ---------------------------------------------------------------------------
# `huminloop status <run_id> --json` — the one contract for "what does this run need".
#
# The approved design doc's Assignment. Before it, five surfaces each inferred this for
# themselves; the skill that drives this CLI was to infer it a sixth time, in prompt text.
# ---------------------------------------------------------------------------

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _status_json(run_id, capsys):
    assert main(["status", run_id, "--json"]) == 0
    return json.loads(capsys.readouterr().out)


def _install_fixture(name, workdir):
    """Put a committed fixture run into a temp root as a real pending run."""
    src = FIXTURES / name
    manifest = json.loads((src / "manifest.json").read_text())
    dst = _artifact_root() / "pending" / manifest["run_id"]
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dst)
    return manifest["run_id"]


def test_status_of_a_clean_pending_run(workdir, capsys):
    assert main(["run", "Define KPIs and a dashboard"]) == 0
    run_id = _run_id_from(capsys.readouterr().out)
    s = _status_json(run_id, capsys)
    assert s["run_id"] == run_id
    assert s["status"] == "pending"
    assert s["needs_resynthesize"] is False
    assert s["unrevised_roles"] == []
    assert s["interrupted"] is False
    assert s["pending_action"] == "approve"


def test_status_fields_stay_inside_their_enums(workdir, capsys):
    """A caller branches on these; a value outside the enum is a silent breakage."""
    assert main(["run", "Define KPIs and a dashboard"]) == 0
    run_id = _run_id_from(capsys.readouterr().out)
    s = _status_json(run_id, capsys)
    assert s["status"] in gate.RUN_STATUSES
    assert s["pending_action"] in gate.PENDING_ACTIONS
    assert set(s) == {
        "run_id",
        "status",
        "needs_resynthesize",
        "flagged_roles",
        "unrevised_roles",
        "interrupted",
        "artifacts_verified",
        "verification_error",
        "pending_action",
    }


def test_status_offers_resynthesize_when_the_lead_came_back_empty(workdir, capsys, monkeypatch):
    """Pattern (a): the one failure that has a fix, so the one that may offer it."""
    import huminloop.cli as cli
    from tests.conftest import RecordingLLM

    monkeypatch.setattr(
        cli, "get_llm", lambda provider=None: RecordingLLM(fail_roles=("engagement_lead",))
    )
    assert main(["run", "Draft an RFP response and SOW"]) == 0
    run_id = _run_id_from(capsys.readouterr().out)

    s = _status_json(run_id, capsys)
    assert s["needs_resynthesize"] is True
    assert s["pending_action"] == "resynthesize"
    assert "engagement_lead" in s["flagged_roles"]

    monkeypatch.setattr(cli, "get_llm", lambda provider=None: RecordingLLM())
    assert main(["resynthesize", run_id]) == 0
    capsys.readouterr()
    after = _status_json(run_id, capsys)
    assert after["needs_resynthesize"] is False
    assert after["pending_action"] == "approve"


def test_status_never_offers_resynthesize_for_an_unrevised_critic(workdir, capsys):
    """Pattern (b), from the run it was actually observed on. No command fixes this, so
    `needs_resynthesize` must not claim to — and the role must still be named."""
    run_id = _install_fixture("unrevised-critic", workdir)
    s = _status_json(run_id, capsys)
    assert s["needs_resynthesize"] is False  # the lead succeeded; resynthesize would refuse
    assert s["unrevised_roles"] == ["governance_advisor"]
    assert s["pending_action"] == "approve"
    # It is otherwise invisible: no error, no process flags, a clean review.
    assert "governance_advisor" not in s["flagged_roles"]


def test_status_reads_the_committed_failed_synthesis_fixture(workdir, capsys):
    """Pattern (a) as a committed manifest, not only as a mock."""
    run_id = _install_fixture("failed-synthesis", workdir)
    s = _status_json(run_id, capsys)
    assert s["needs_resynthesize"] is True
    assert s["pending_action"] == "resynthesize"
    assert s["unrevised_roles"] == []  # the lead errored; that is pattern (a), not (b)


def test_status_reports_flagged_and_approvable_at_once(workdir, capsys, monkeypatch):
    """The design doc is explicit that these two are independent. A flag is something to look
    at, not a block on reaching the decision."""
    import huminloop.cli as cli

    monkeypatch.setattr(cli, "get_llm", lambda provider=None: JunkLLM())
    assert main(["run", "Define KPIs"]) == 0
    run_id = _run_id_from(capsys.readouterr().out)
    s = _status_json(run_id, capsys)
    assert s["flagged_roles"]
    assert s["needs_resynthesize"] is False
    assert s["pending_action"] == "approve"


def test_status_of_a_decided_run_is_done(workdir, capsys):
    assert main(["run", "Define KPIs and a dashboard"]) == 0
    run_id = _run_id_from(capsys.readouterr().out)
    assert main(["approve", run_id, "--by", "Tony"]) == 0
    capsys.readouterr()
    s = _status_json(run_id, capsys)
    assert s["status"] == "approved" and s["pending_action"] == "done"

    assert main(["reopen", run_id, "--by", "Tony", "--reason", "second look"]) == 0
    capsys.readouterr()
    assert _status_json(run_id, capsys)["pending_action"] == "approve"


def test_status_of_a_rejected_run_is_done(workdir, capsys):
    assert main(["run", "Define KPIs and a dashboard"]) == 0
    run_id = _run_id_from(capsys.readouterr().out)
    assert main(["reject", run_id, "--by", "Tony", "--reason", "wrong framing"]) == 0
    capsys.readouterr()
    s = _status_json(run_id, capsys)
    assert s["status"] == "rejected" and s["pending_action"] == "done"


def test_status_says_wait_while_a_live_orchestrator_holds_the_run(workdir, capsys):
    assert main(["run", "Define KPIs and a dashboard"]) == 0
    run_id = _run_id_from(capsys.readouterr().out)
    (_artifact_root() / "pending" / run_id / "run.lock").write_text(str(os.getpid()))
    s = _status_json(run_id, capsys)
    assert s["status"] == "running" and s["pending_action"] == "wait"
    assert s["needs_resynthesize"] is False  # never offer a retry against a live run


def test_status_tells_an_interrupted_run_to_be_rejected_not_approved(workdir, capsys):
    """`approve` refuses these by name, so reporting "approve" would be handing out an answer
    the next command contradicts."""
    d = _artifact_root() / "pending" / "20260101_000000_abcdef"
    d.mkdir(parents=True)
    (d / "manifest.json").write_text(
        '{"run_id": "20260101_000000_abcdef", "task": "t", "status": "running", "artifacts": []}'
    )
    s = _status_json("20260101_000000_abcdef", capsys)
    assert s["interrupted"] is True
    assert s["pending_action"] == "reject"
    assert s["needs_resynthesize"] is False  # nothing survived to synthesize from
    assert main(["approve", "20260101_000000_abcdef", "--by", "Tony"]) == 2
    assert "interrupted" in capsys.readouterr().err


def test_status_surfaces_an_unknown_run_instead_of_inventing_a_state(workdir, capsys):
    assert main(["status", "20260101_000000_ffffff", "--json"]) == 2
    err = capsys.readouterr().err
    assert "not found" in err and "Traceback" not in err

    assert main(["status", "../../etc", "--json"]) == 2
    assert "invalid run_id" in capsys.readouterr().err


def test_status_surfaces_a_corrupt_manifest_rather_than_a_state(workdir, capsys):
    d = _artifact_root() / "pending" / "20260101_000000_bbbbbb"
    d.mkdir(parents=True)
    (d / "manifest.json").write_text("{not json at all")
    assert main(["status", "20260101_000000_bbbbbb", "--json"]) == 2
    assert "Traceback" not in capsys.readouterr().err


def test_status_without_json_prints_the_command_to_run_next(workdir, capsys, monkeypatch):
    import huminloop.cli as cli
    from tests.conftest import RecordingLLM

    monkeypatch.setattr(
        cli, "get_llm", lambda provider=None: RecordingLLM(fail_roles=("engagement_lead",))
    )
    assert main(["run", "Draft an RFP response and SOW"]) == 0
    run_id = _run_id_from(capsys.readouterr().out)
    assert main(["status", run_id]) == 0
    out = capsys.readouterr().out
    assert f"huminloop resynthesize {run_id}" in out
    assert "came back empty" in out


def test_status_names_an_unrevised_role_and_offers_no_fix_for_it(workdir, capsys):
    run_id = _install_fixture("unrevised-critic", workdir)
    assert main(["status", run_id]) == 0
    out = capsys.readouterr().out
    assert "governance_advisor" in out
    assert "no recovery command exists" in out
    assert "resynthesize" not in out  # never offer a fix that would not work


def test_engagement_list_shows_a_corrupt_one_rather_than_hiding_it(workdir, engagements, capsys):
    assert main(["engagement", "new", "Acme"]) == 0
    (engagements / "acme" / "engagement.json").write_text("{ not json")
    capsys.readouterr()
    assert main(["engagement", "list"]) == 0
    out = capsys.readouterr().out
    assert "acme" in out and "CORRUPT" in out


def test_the_clearance_prompt_states_what_it_will_cost(workdir, engagements, capsys):
    """Context now rides every seat's draft, critique and revision. "Yes" to one call and
    "yes" to thirty are different answers."""
    assert main(["engagement", "new", "Acme"]) == 0
    (engagements / "acme" / "context" / "discovery.md").write_text("Acme Corp, 400 techs.")
    capsys.readouterr()
    assert main(["--engagement", "acme", "run", "Draft an RFP response and SOW"]) == 2
    err = capsys.readouterr().err
    assert "provider call(s)" in err
    assert "seat(s)" in err
    assert "engagement_lead" in err  # the lead is counted, not forgotten
    assert str(engagements / "acme" / "context") in err  # an absolute path, not "context"


def test_a_context_file_far_over_budget_is_not_read_whole(workdir, engagements, monkeypatch):
    """read_text() pulled the entire file in before discovering almost none of it fit."""
    from huminloop import engagement as eng

    assert main(["engagement", "new", "Acme"]) == 0
    big = engagements / "acme" / "context" / "huge.md"
    big.write_text("z" * 200_000)

    reads = []
    real_open = Path.open

    def spy(self, *a, **k):
        handle = real_open(self, *a, **k)
        if self == big:
            real_read = handle.read

            def capped(n=-1):
                reads.append(n)
                return real_read(n)

            handle.read = capped
        return handle

    monkeypatch.setattr(Path, "open", spy)
    ctx = eng.prepare_context(engagements / "acme", budget=500)
    assert reads and max(reads) <= 501  # the budget, plus one to detect the overflow
    assert ctx.read[0]["state"] == "truncated"
    assert ctx.chars < 1000


# ---------------------------------------------------------------------------
# The interactive half of the clearance gate — the place a human actually answers
# "may this client material go to the provider", and the least-tested line in the change.
# ---------------------------------------------------------------------------


def _engagement_with_context(engagements, text="Acme Corp, 400 field techs."):
    assert main(["engagement", "new", "Acme"]) == 0
    (engagements / "acme" / "context" / "discovery.md").write_text(text)
    return engagements / "acme"


@pytest.mark.parametrize("answer", ["n", "no", "", "  ", "yes please but actually no"])
def test_anything_but_yes_at_the_clearance_prompt_sends_nothing(
    workdir, engagements, capsys, monkeypatch, answer
):
    """Deleting the refusal branch left all 321 tests green — the CLI would have sent client
    material whatever the human typed."""
    root = _engagement_with_context(engagements)
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("builtins.input", lambda _p: answer)
    capsys.readouterr()

    assert main(["--engagement", "acme", "run", "Design the program"]) == 2
    assert "not cleared" in capsys.readouterr().err
    assert not list((root / "out").rglob("manifest.json"))  # nothing ran at all


def test_saying_yes_at_the_prompt_records_who_said_it(workdir, engagements, capsys, monkeypatch):
    root = _engagement_with_context(engagements)
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("builtins.input", lambda _p: "y")
    capsys.readouterr()

    assert main(["--engagement", "acme", "run", "Define KPIs", "--cleared-by", "Tony"]) == 0
    m = json.loads(next((root / "out").rglob("manifest.json")).read_text())
    assert m["context_clearance"]["method"] == "prompt"
    assert m["context_clearance"]["by"] == "Tony"


def test_the_prompt_shows_the_summary_before_it_asks(workdir, engagements, capsys, monkeypatch):
    _engagement_with_context(engagements)
    seen = {}
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("builtins.input", lambda p: seen.setdefault("prompt", p) and "n")
    capsys.readouterr()

    main(["--engagement", "acme", "run", "Define KPIs"])
    out = capsys.readouterr().out
    assert "discovery.md" in out and "provider call(s)" in out
    assert "Tony" not in seen.get("prompt", "")  # no --cleared-by given


def test_the_clearance_identity_defaults_to_the_os_user(workdir, engagements, capsys):
    import getpass

    root = _engagement_with_context(engagements)
    capsys.readouterr()
    assert main(["--engagement", "acme", "run", "Define KPIs", "--context-cleared"]) == 0
    m = json.loads(next((root / "out").rglob("manifest.json")).read_text())
    assert m["context_clearance"]["by"] == getpass.getuser()
    assert m["context_clearance"]["method"] == "--context-cleared"


def test_a_crafted_filename_cannot_rewrite_the_consent_prompt(workdir, engagements, capsys):
    """The summary is what a human reads before answering. ANSI escapes in a filename could
    scroll the real rows out of view."""
    assert main(["engagement", "new", "Acme"]) == 0
    (engagements / "acme" / "context" / "innocent\x1b[2J\x1b[H.md").write_text("client notes")
    capsys.readouterr()
    assert main(["--engagement", "acme", "run", "Define KPIs"]) == 2
    err = capsys.readouterr().err
    assert "\x1b" not in err
    assert "innocent" in err  # still named, just defanged


def test_the_quoted_call_count_matches_the_run_that_was_actually_asked_for(
    workdir, engagements, capsys
):
    """--no-critique makes one call per seat, not three. A wrong number on a consent prompt is
    a wrong number a human is relying on."""
    _engagement_with_context(engagements)
    capsys.readouterr()
    main(["--engagement", "acme", "run", "Draft an RFP response and SOW"])
    with_critique = capsys.readouterr().err

    main(["--engagement", "acme", "run", "Draft an RFP response and SOW", "--no-critique"])
    without = capsys.readouterr().err

    def calls(text):
        return int(text.split("over up to ")[1].split(" provider")[0])

    assert calls(with_critique) == calls(without) * 3


def test_every_pending_action_has_a_command_to_print():
    """Renaming a _NEXT_COMMAND key left all tests green while `status` would KeyError."""
    from huminloop import cli

    assert set(cli._NEXT_COMMAND) == set(gate.PENDING_ACTIONS)


def test_status_of_a_recorded_but_incomplete_decision_names_that_same_decision(
    workdir, capsys, failing_rename
):
    """A decision written to the manifest whose directory move failed. Reporting 'approve'
    here would be the status/command contradiction the enum exists to end."""
    assert main(["run", "Define KPIs and a dashboard"]) == 0
    run_id = _run_id_from(capsys.readouterr().out)

    break_rename, restore = failing_rename
    break_rename()
    with pytest.raises(OSError):
        gate.reject(run_id, by="Tony", reason="wrong framing")
    restore()

    s = _status_json(run_id, capsys)
    assert s["status"] == "pending"  # still in pending/ on disk
    assert s["pending_action"] == "reject"  # the recorded decision, not a fresh approve
    assert main(["status", run_id]) == 0
    assert f"huminloop reject {run_id}" in capsys.readouterr().out


def test_status_prose_says_an_interrupted_run_cannot_be_approved(workdir, capsys):
    d = _artifact_root() / "pending" / "20260101_000000_cccccc"
    d.mkdir(parents=True)
    (d / "manifest.json").write_text(
        '{"run_id": "20260101_000000_cccccc", "task": "t", "status": "running", "artifacts": []}'
    )
    assert main(["status", "20260101_000000_cccccc"]) == 0
    out = capsys.readouterr().out
    assert "died before it finished" in out
    assert "huminloop reject 20260101_000000_cccccc" in out


def test_a_newline_in_a_filename_cannot_forge_rows_in_the_consent_prompt(
    workdir, engagements, capsys
):
    """strip_controls keeps newlines by design (it sanitises prose). A POSIX filename may
    contain one, so the first fix left the attack open.

    The first version of this test asserted `len(rows) == 2`, which passes against the
    vulnerable code: the forged row simply takes the place of the real one in the count.
    Assert the transformation instead -- the whole hostile name must stay on ONE physical
    line, with its newline shown rather than obeyed.
    """
    assert main(["engagement", "new", "Acme"]) == 0
    ctx = engagements / "acme" / "context"
    (ctx / "ordinary.md").write_text("real notes")
    hostile = "a.md\n  master-services-agreement.md            read\x1b[2K\nz.md"
    (ctx / hostile).write_text("x")
    capsys.readouterr()

    assert main(["--engagement", "acme", "run", "Define KPIs"]) == 2
    err = capsys.readouterr().err

    line = next(ln for ln in err.splitlines() if "master-services-agreement" in ln)
    assert "a.md" in line and "z.md" in line, "the hostile name was split across rows"
    assert "\\n" in line  # the newline is shown escaped, not acted on
    assert "\x1b" not in err  # and the escape sequence never reaches the terminal
    assert "ordinary.md" in err  # the real file is still listed


def test_status_refuses_to_recommend_approving_a_tampered_run(workdir, capsys, tmp_path):
    """`status` said `approve` while `approve` refused on the bytes -- the command
    contradicting the very next command, which is the failure pending_action exists to
    prevent. Fixed for interrupted runs in this same branch and missed here."""
    assert main(["run", "Define KPIs and a dashboard"]) == 0
    run_id = _run_id_from(capsys.readouterr().out)
    art = next((_artifact_root() / "pending" / run_id).glob("*.md"))
    art.write_text(art.read_text() + "\nSmuggled in after the run.\n")

    s = _status_json(run_id, capsys)
    assert s["artifacts_verified"] is False
    assert "changed since the run" in s["verification_error"]
    assert s["pending_action"] == "reject"  # not approve: the gate will refuse that
    assert s["needs_resynthesize"] is False  # and resynthesizing cannot repair bytes

    # The recommendation and the gate now agree.
    assert main(["approve", run_id, "--by", "Tony"]) == 2
    assert "changed since the run" in capsys.readouterr().err
    assert main(["status", run_id]) == 0
    out = capsys.readouterr().out
    assert "artifacts not verified" in out and "changed since the run" in out
    assert f"huminloop reject {run_id}" in out


def test_status_and_pending_agree_that_a_manifestless_run_exists(workdir, capsys):
    """`pending` listed it as "incomplete (no manifest)" while `status` said "not found" --
    two gate surfaces disagreeing that a run exists at all."""
    d = _artifact_root() / "pending" / "20260101_000000_aaaaaa"
    d.mkdir(parents=True)

    assert main(["pending"]) == 0
    assert "20260101_000000_aaaaaa" in capsys.readouterr().out

    s = _status_json("20260101_000000_aaaaaa", capsys)
    assert s["run_id"] == "20260101_000000_aaaaaa"
    assert s["status"] == "pending"
    assert s["interrupted"] is True
    assert s["pending_action"] == "reject"  # a human clears it; it cannot be approved
    assert main(["approve", "20260101_000000_aaaaaa", "--by", "Tony"]) == 2


def test_a_clean_pending_run_reports_its_artifacts_verified(workdir, capsys):
    """The other side: don't start telling every honest run its bytes are suspect."""
    assert main(["run", "Define KPIs and a dashboard"]) == 0
    run_id = _run_id_from(capsys.readouterr().out)
    s = _status_json(run_id, capsys)
    assert s["artifacts_verified"] is True
    assert s["verification_error"] == ""
    assert s["pending_action"] == "approve"


def test_every_status_path_answers_with_the_same_shape(workdir, capsys, failing_rename):
    """`status` had two return statements; a commit added two fields to one and not the other,
    so a caller reading `artifacts_verified` on a manifest-less run got a KeyError -- from the
    command whose whole purpose is being the one shape a caller can rely on. Assert the shape
    across every path, not just the happy one."""
    shapes = {}

    # 1. a clean pending run
    assert main(["run", "Define KPIs and a dashboard"]) == 0
    clean_id = _run_id_from(capsys.readouterr().out)
    shapes["clean pending"] = _status_json(clean_id, capsys)

    # 2. a run that died before its first manifest write
    (_artifact_root() / "pending" / "20260101_000000_aaaaaa").mkdir(parents=True)
    shapes["no manifest"] = _status_json("20260101_000000_aaaaaa", capsys)

    # 3. an interrupted run that has a manifest
    d = _artifact_root() / "pending" / "20260101_000000_bbbbbb"
    d.mkdir(parents=True)
    (d / "manifest.json").write_text(
        '{"run_id": "20260101_000000_bbbbbb", "task": "t", "status": "running", "artifacts": []}'
    )
    shapes["interrupted"] = _status_json("20260101_000000_bbbbbb", capsys)

    # 4. a tampered run
    assert main(["run", "Define KPIs and a dashboard"]) == 0
    tampered_id = _run_id_from(capsys.readouterr().out)
    art = next((_artifact_root() / "pending" / tampered_id).glob("*.md"))
    art.write_text(art.read_text() + "\ntampered\n")
    shapes["tampered"] = _status_json(tampered_id, capsys)

    # 5. a decided run
    assert main(["approve", clean_id, "--by", "Tony"]) == 0
    capsys.readouterr()
    shapes["approved"] = _status_json(clean_id, capsys)

    expected = set(shapes["clean pending"])
    for label, s in shapes.items():
        assert set(s) == expected, f"{label} answers with a different shape"
        assert s["status"] in gate.RUN_STATUSES, label
        assert s["pending_action"] in gate.PENDING_ACTIONS, label
        # Every field a caller might branch on is present and typed, on every path.
        assert isinstance(s["artifacts_verified"], bool), label
        assert isinstance(s["verification_error"], str), label
        assert isinstance(s["flagged_roles"], list), label

    # And the paths genuinely differ, or this test proves nothing.
    assert shapes["no manifest"]["pending_action"] == "reject"
    assert shapes["tampered"]["artifacts_verified"] is False
    assert shapes["approved"]["pending_action"] == "done"

    # `artifacts_verified` is a claim, so it may only be true where a check actually ran and
    # passed. It defaulted to true once, and three paths claimed checks nobody ran.
    assert shapes["clean pending"]["artifacts_verified"] is True
    assert shapes["approved"]["artifacts_verified"] is True  # checked, and clean
    assert shapes["no manifest"]["artifacts_verified"] is False
    assert "no manifest" in shapes["no manifest"]["verification_error"]
    for label, s in shapes.items():
        # Never "unverified" without saying why, never "verified" while carrying an error.
        assert bool(s["verification_error"]) is (not s["artifacts_verified"]), label


def test_an_approved_run_edited_after_approval_is_not_reported_verified(workdir, capsys):
    """`status` only checked pending runs, so an approved deliverable edited after approval --
    exactly the tampering this record exists to reveal -- reported itself verified."""
    assert main(["run", "Define KPIs and a dashboard"]) == 0
    run_id = _run_id_from(capsys.readouterr().out)
    assert main(["approve", run_id, "--by", "Tony"]) == 0
    capsys.readouterr()
    art = next((_artifact_root() / "approved" / run_id).glob("*.md"))
    art.write_text(art.read_text() + "\nedited after approval\n")

    s = _status_json(run_id, capsys)
    assert s["status"] == "approved"
    assert s["pending_action"] == "done"  # decided is decided; the record just tells the truth
    assert s["artifacts_verified"] is False
    assert "changed since the run" in s["verification_error"]


def test_a_live_run_is_not_reported_verified(workdir, capsys):
    """A run still being written cannot be checked, and must say so rather than borrow a
    result."""
    assert main(["run", "Define KPIs and a dashboard"]) == 0
    run_id = _run_id_from(capsys.readouterr().out)
    (_artifact_root() / "pending" / run_id / "run.lock").write_text(str(os.getpid()))
    s = _status_json(run_id, capsys)
    assert s["status"] == "running"
    assert s["artifacts_verified"] is False
    assert "in progress" in s["verification_error"]


# The property the status contract promises, checked for every state rather than one command at
# a time. The first tampered-run test ran `approve` after `status` said `reject`, confirmed the
# refusal, and never ran `reject` — which also refused, leaving the run with no legal move.


def _edit_artifact(rid):
    art = next((_artifact_root() / "pending" / rid).glob("*.md"))
    art.write_text(art.read_text() + "\nSmuggled in after the run.\n")


def _binary_artifact(rid):
    next((_artifact_root() / "pending" / rid).glob("*.md")).write_bytes(b"\xff\xfe\x00binary")


def _record_then_edit(decision):
    def setup(rid, failing_rename):
        break_rename, restore = failing_rename
        break_rename()
        with pytest.raises(OSError):
            if decision == "approve":
                gate.approve(rid, by="Tony")
            else:
                gate.reject(rid, by="Tony", reason="first look")
        restore()
        _edit_artifact(rid)

    return setup


def _interrupt(rid, failing_rename):
    mf = _artifact_root() / "pending" / rid / "manifest.json"
    mf.write_text(json.dumps(json.loads(mf.read_text()) | {"status": "running"}))


def _lose_manifest(rid, failing_rename):
    (_artifact_root() / "pending" / rid / "manifest.json").unlink()


_STATES = {
    "clean": (lambda rid, fr: None, "approve"),
    "interrupted": (_interrupt, "reject"),
    "no manifest": (_lose_manifest, "reject"),
    "edited": (lambda rid, fr: _edit_artifact(rid), "reject"),
    "binary": (lambda rid, fr: _binary_artifact(rid), "reject"),
    "recorded approve, then edited": (_record_then_edit("approve"), "reject"),
    "recorded reject, then edited": (_record_then_edit("reject"), "reject"),
}


@pytest.mark.parametrize("name", list(_STATES))
def test_the_command_status_recommends_is_one_the_gate_accepts(
    workdir, capsys, failing_rename, name
):
    setup, expected = _STATES[name]
    assert main(["run", "Define KPIs and a dashboard"]) == 0
    rid = _run_id_from(capsys.readouterr().out)
    setup(rid, failing_rename)

    action = _status_json(rid, capsys)["pending_action"]
    assert action == expected
    cmd = ["approve", rid, "--by", "Tony"]
    if action == "reject":
        cmd = ["reject", rid, "--by", "Tony", "--reason", "failed verification"]
    assert main(cmd) == 0, capsys.readouterr().err
    capsys.readouterr()
    assert _status_json(rid, capsys)["pending_action"] == "done"


def test_a_reject_of_an_unverified_run_records_why(workdir, capsys):
    assert main(["run", "Define KPIs and a dashboard"]) == 0
    rid = _run_id_from(capsys.readouterr().out)
    _edit_artifact(rid)
    assert main(["reject", rid, "--by", "Tony", "--reason", "edited"]) == 0
    m = json.loads((_artifact_root() / "rejected" / rid / "manifest.json").read_text())
    assert "changed since the run" in m["decision"]["verification_error"]


def test_an_unverified_run_still_cannot_be_approved(workdir, capsys):
    """Allowing reject must not have loosened approve."""
    assert main(["run", "Define KPIs and a dashboard"]) == 0
    rid = _run_id_from(capsys.readouterr().out)
    _binary_artifact(rid)
    assert main(["approve", rid, "--by", "Tony"]) == 2
    assert "cannot be read as text" in capsys.readouterr().err
    assert (_artifact_root() / "pending" / rid).is_dir()


def test_a_reject_supersedes_a_recorded_approval_without_erasing_it(
    workdir, capsys, failing_rename
):
    assert main(["run", "Define KPIs and a dashboard"]) == 0
    rid = _run_id_from(capsys.readouterr().out)
    _record_then_edit("approve")(rid, failing_rename)
    assert main(["reject", rid, "--by", "Dana", "--reason", "edited after approval"]) == 0
    m = json.loads((_artifact_root() / "rejected" / rid / "manifest.json").read_text())
    assert [d["state"] for d in m["decisions"]] == ["approved", "rejected"]
    assert m["decision"]["by"] == "Dana"
    assert m["decision"]["supersedes"]["state"] == "approved"
    assert m["status"] == "rejected"
    # Dana made a new decision; she did not complete Tony's. The log must not say she did.
    last = json.loads(log_path().read_text().splitlines()[-1])
    assert last["event"] == "rejected" and last["by"] == "Dana" and last["completed_by"] is None


def test_a_verified_recorded_approval_still_refuses_a_different_decision(
    workdir, capsys, failing_rename
):
    """Supersession is only for bytes that fail the check; otherwise the recorded one stands."""
    assert main(["run", "Define KPIs and a dashboard"]) == 0
    rid = _run_id_from(capsys.readouterr().out)
    break_rename, restore = failing_rename
    break_rename()
    with pytest.raises(OSError):
        gate.approve(rid, by="Tony")
    restore()
    assert main(["reject", rid, "--by", "Dana", "--reason", "changed my mind"]) == 2
    assert "already has a recorded approved" in capsys.readouterr().err


def test_status_of_an_approved_run_whose_file_is_no_longer_text(workdir, capsys):
    """It exited 2 with a codec error instead of reporting the edit it exists to reveal."""
    assert main(["run", "Define KPIs and a dashboard"]) == 0
    rid = _run_id_from(capsys.readouterr().out)
    assert main(["approve", rid, "--by", "Tony"]) == 0
    capsys.readouterr()
    next((_artifact_root() / "approved" / rid).glob("*.md")).write_bytes(b"\xff\xfe\x00")
    s = _status_json(rid, capsys)
    assert s["artifacts_verified"] is False
    assert "cannot be read as text" in s["verification_error"]
    assert s["pending_action"] == "done"


# The manifest is editable, so every field verification reads from it is part of the attack
# surface. Each of these used to verify, or to crash every command, instead of failing the check.


def _edit_manifest(rid, fn):
    mf = _artifact_root() / "pending" / rid / "manifest.json"
    m = json.loads(mf.read_text())
    fn(m)
    mf.write_text(json.dumps(m))


def _first_file(m):
    return next(a for a in m["artifacts"] if a.get("file"))


def test_a_manifest_without_digests_does_not_verify(workdir, capsys):
    """Dropping `sha256` used to switch the byte check off entirely."""
    assert main(["run", "Define KPIs and a dashboard"]) == 0
    rid = _run_id_from(capsys.readouterr().out)
    _edit_manifest(rid, lambda m: [a.pop("sha256", None) for a in m["artifacts"]])
    s = _status_json(rid, capsys)
    assert s["artifacts_verified"] is False and "no recorded sha256" in s["verification_error"]
    assert s["pending_action"] == "reject"
    with pytest.raises(gate.GateError, match="no recorded sha256"):
        gate.approve(rid, by="Tony")


@pytest.mark.parametrize("how", ["absolute", "dotdot", "symlink"])
def test_an_artifact_outside_the_run_does_not_verify(workdir, capsys, tmp_path, how):
    """A file the run never wrote, with a matching digest, must still be refused."""
    assert main(["run", "Define KPIs and a dashboard"]) == 0
    rid = _run_id_from(capsys.readouterr().out)
    d = _artifact_root() / "pending" / rid
    first = _first_file(json.loads((d / "manifest.json").read_text()))
    outside = tmp_path / "outside.md"
    outside.write_text((d / first["file"]).read_text())  # same bytes, same digest
    if how == "symlink":
        (d / first["file"]).unlink()
        (d / first["file"]).symlink_to(outside)
    else:
        target = str(outside) if how == "absolute" else os.path.relpath(outside, d)
        _edit_manifest(rid, lambda m: _first_file(m).update(file=target))
    with pytest.raises(gate.GateError, match="outside the run directory"):
        gate.approve(rid, by="Tony")
    assert _status_json(rid, capsys)["pending_action"] == "reject"
    assert main(["reject", rid, "--by", "Tony", "--reason", "outside"]) == 0


@pytest.mark.parametrize(
    "edit",
    [lambda a: a.update(review="x"), lambda a: a.update(file=5)],
    ids=["review-not-a-mapping", "file-not-a-string"],
)
def test_a_malformed_artifact_entry_can_still_be_rejected(workdir, capsys, edit):
    """These raised AttributeError/TypeError from status and reject alike: no way out."""
    assert main(["run", "Define KPIs and a dashboard"]) == 0
    rid = _run_id_from(capsys.readouterr().out)
    _edit_manifest(rid, lambda m: edit(_first_file(m)))
    s = _status_json(rid, capsys)
    assert s["pending_action"] == "reject" and "malformed" in s["verification_error"]
    assert main(["reject", rid, "--by", "Tony", "--reason", "malformed"]) == 0


def test_an_unreadable_artifact_fails_the_check(workdir, capsys):
    if os.geteuid() == 0:
        pytest.skip("root reads anything")
    assert main(["run", "Define KPIs and a dashboard"]) == 0
    rid = _run_id_from(capsys.readouterr().out)
    art = next((_artifact_root() / "pending" / rid).glob("*.md"))
    art.chmod(0)
    try:
        s = _status_json(rid, capsys)
        assert "cannot be read as text" in s["verification_error"]
        assert s["pending_action"] == "reject"
    finally:
        art.chmod(0o644)


def test_only_one_reject_may_supersede_a_recorded_approval(workdir, capsys, failing_rename):
    """Two supersedes both wrote the manifest; one decision vanished and the log disagreed."""
    assert main(["run", "Define KPIs and a dashboard"]) == 0
    rid = _run_id_from(capsys.readouterr().out)
    _record_then_edit("approve")(rid, failing_rename)
    d = _artifact_root() / "pending" / rid
    (d / gate.SUPERSEDE_CLAIM).touch()  # another process is mid-supersede
    with pytest.raises(gate.GateError, match="being decided by another process"):
        gate.reject(rid, by="Bea", reason="edited")
    (d / gate.SUPERSEDE_CLAIM).unlink()
    gate.reject(rid, by="Ann", reason="edited")
    # Reopening clears it, or the next supersede on this run would be refused forever.
    gate.reopen(rid, by="Ann", reason="look again")
    assert not (d / gate.SUPERSEDE_CLAIM).exists()


def test_a_recorded_reject_on_edited_bytes_is_completed_not_superseded(
    workdir, capsys, failing_rename
):
    """Supersession is only for a recorded approval; a recorded reject is finished as written."""
    assert main(["run", "Define KPIs and a dashboard"]) == 0
    rid = _run_id_from(capsys.readouterr().out)
    _record_then_edit("reject")(rid, failing_rename)
    assert main(["reject", rid, "--by", "Dana", "--reason", "second look"]) == 0
    m = json.loads((_artifact_root() / "rejected" / rid / "manifest.json").read_text())
    assert [d["state"] for d in m["decisions"]] == ["rejected"]
    assert m["decision"]["by"] == "Tony" and m["decision"]["note"] == "first look"
    assert "supersedes" not in m["decision"]
    last = json.loads(log_path().read_text().splitlines()[-1])
    assert last["event"] == "rejected" and last["completed_by"] == "Dana"


def test_a_supersede_names_who_it_replaced_and_when(workdir, capsys, failing_rename):
    assert main(["run", "Define KPIs and a dashboard"]) == 0
    rid = _run_id_from(capsys.readouterr().out)
    _record_then_edit("approve")(rid, failing_rename)
    assert main(["reject", rid, "--by", "Dana", "--reason", "edited after approval"]) == 0
    m = json.loads((_artifact_root() / "rejected" / rid / "manifest.json").read_text())
    approval = m["decisions"][0]
    assert m["decision"]["supersedes"] == {
        "state": "approved",
        "by": approval["by"],
        "at": approval["at"],
    }
    assert approval["by"] == "Tony" and approval["at"]


def test_a_recorded_approval_whose_bytes_still_verify_is_finished_by_approve(
    workdir, capsys, failing_rename
):
    """Only failed bytes turn a recorded approval into a reject; intact ones complete it."""
    assert main(["run", "Define KPIs and a dashboard"]) == 0
    rid = _run_id_from(capsys.readouterr().out)
    break_rename, restore = failing_rename
    break_rename()
    with pytest.raises(OSError):
        gate.approve(rid, by="Tony")
    restore()
    s = _status_json(rid, capsys)
    assert s["artifacts_verified"] is True and s["pending_action"] == "approve"
    assert main(["approve", rid, "--by", "Dana"]) == 0
    capsys.readouterr()
    assert _status_json(rid, capsys)["status"] == "approved"


def test_an_empty_digest_is_reported_as_missing(workdir, capsys):
    """An emptied `sha256` must name the edit, not blame the artifact's bytes."""
    assert main(["run", "Define KPIs and a dashboard"]) == 0
    rid = _run_id_from(capsys.readouterr().out)
    _edit_manifest(rid, lambda m: _first_file(m).update(sha256=""))
    s = _status_json(rid, capsys)
    assert s["artifacts_verified"] is False and "no recorded sha256" in s["verification_error"]
    assert s["pending_action"] == "reject"


# Second review round: one-field manifest edits that still crashed `status` and `reject` with an
# exception other than GateError, and one that skipped verification outright.


def _loop(rid):
    art = next((_artifact_root() / "pending" / rid).glob("*.md"))
    art.unlink()
    art.symlink_to(art)  # RuntimeError from Path.resolve on 3.12, not OSError


def _edit_decision(rid, **fields):
    base = {"state": "approved", "by": "T", "at": "2026-09-18T00:00:00+00:00", "note": ""}
    _edit_manifest(rid, lambda m: m.update(decision=base | fields))


def _falsey_review_on_flagged_bytes(rid):
    """`review: ""` used to read as `{}`; it only verified when the bytes' own review failed."""
    d = _artifact_root() / "pending" / rid

    def edit(m):
        a = _first_file(m)
        (d / a["file"]).write_text("not a deliverable")  # fails review: no sections
        a.update(review="", sha256=sha256_text("not a deliverable"))

    _edit_manifest(rid, edit)


def _error_beside_edited_file(rid):
    """`error` on the very artifact whose bytes were replaced skipped every check on it."""
    d = _artifact_root() / "pending" / rid

    def edit(m):
        a = _first_file(m)
        (d / a["file"]).write_text("replaced after the run")
        a.update(error="boom")

    _edit_manifest(rid, edit)


_CRASHERS = {
    "symlink loop": _loop,
    "null byte in file": lambda rid: _edit_manifest(
        rid, lambda m: _first_file(m).update(file="a\x00.md")
    ),
    "overlong file": lambda rid: _edit_manifest(
        rid, lambda m: _first_file(m).update(file="x" * 300)
    ),
    "falsey review": _falsey_review_on_flagged_bytes,
    "decision is a string": lambda rid: _edit_manifest(
        rid, lambda m: m.update(decision="approved")
    ),
    "decisions is a dict": lambda rid: _edit_manifest(rid, lambda m: m.update(decisions={})),
    # Round 2: a mapping that is not a decision the gate wrote passed one copy of the shape rule
    # and failed the next, so `status` recommended a move the gate then refused.
    "decision state is a number": lambda rid: _edit_decision(rid, state=5),
    "decision state is a list": lambda rid: _edit_decision(rid, state=["approved"]),
    "decision state is null": lambda rid: _edit_decision(rid, state=None),
    "decision state is unknown": lambda rid: _edit_decision(rid, state="blocked"),
    "decision has no state": lambda rid: _edit_manifest(
        rid, lambda m: m.update(decision={"by": "x"})
    ),
    "decision name is a number": lambda rid: _edit_decision(rid, by=5),
    "decision time is a number": lambda rid: _edit_decision(rid, at=5),
    "decision note is a list": lambda rid: _edit_decision(rid, note=["x"]),
    # Round 3: a recorded decision naming nobody would move the run with no named approver.
    "decision names nobody": lambda rid: _edit_manifest(
        rid, lambda m: m.update(decision={"state": "approved"})
    ),
    "decision name is blank": lambda rid: _edit_decision(rid, by="  "),
    "decisions holds a non-mapping": lambda rid: _edit_manifest(
        rid, lambda m: m.update(decisions=["x"])
    ),
    "error beside a file": _error_beside_edited_file,
}


@pytest.mark.parametrize("name", list(_CRASHERS))
def test_every_manifest_edit_leaves_reject_as_a_way_out(workdir, capsys, name):
    assert main(["run", "Define KPIs and a dashboard"]) == 0
    rid = _run_id_from(capsys.readouterr().out)
    _CRASHERS[name](rid)
    s = _status_json(rid, capsys)
    assert s["artifacts_verified"] is False and s["pending_action"] == "reject", s
    with pytest.raises(gate.GateError, match="refusing to approve"):
        gate.approve(rid, by="Tony", note="override", force=True)
    assert main(["reject", rid, "--by", "Tony", "--reason", name]) == 0, capsys.readouterr().err
    m = json.loads((_artifact_root() / "rejected" / rid / "manifest.json").read_text())
    assert m["decision"]["verification_error"]


def test_a_malformed_decision_is_kept_not_erased(workdir, capsys):
    assert main(["run", "Define KPIs and a dashboard"]) == 0
    rid = _run_id_from(capsys.readouterr().out)
    _edit_manifest(rid, lambda m: m.update(decision="approved", decisions={"x": 1}))
    gate.reject(rid, by="Tony", reason="malformed")
    m = json.loads((_artifact_root() / "rejected" / rid / "manifest.json").read_text())
    assert m["decision_malformed"] == "approved" and m["decisions_malformed"] == {"x": 1}
    assert [d["state"] for d in m["decisions"]] == ["rejected"]


@pytest.mark.parametrize("decision", ["approve", "reject"])
def test_a_failed_write_does_not_leave_a_claim_behind(
    workdir, capsys, failing_rename, monkeypatch, decision
):
    """A claim that outlived a failed attempt refused every later decision, forever."""
    assert main(["run", "Define KPIs and a dashboard"]) == 0
    rid = _run_id_from(capsys.readouterr().out)
    d = _artifact_root() / "pending" / rid
    if decision == "reject":
        _record_then_edit("approve")(rid, failing_rename)  # the supersede path
    real = gate.write_manifest
    monkeypatch.setattr(gate, "write_manifest", lambda *a: (_ for _ in ()).throw(OSError("full")))
    with pytest.raises(OSError):
        if decision == "approve":
            gate.approve(rid, by="Tony")
        else:
            gate.reject(rid, by="Ann", reason="edited")
    monkeypatch.setattr(gate, "write_manifest", real)
    assert not (d / gate.DECISION_CLAIM).exists() or decision == "reject"
    assert not (d / gate.SUPERSEDE_CLAIM).exists()
    if decision == "approve":
        gate.approve(rid, by="Tony")
    else:
        gate.reject(rid, by="Ann", reason="edited")


def test_the_log_records_a_supersede(workdir, capsys, failing_rename):
    """The manifest is the editable file; the override has to be visible in the log too."""
    assert main(["run", "Define KPIs and a dashboard"]) == 0
    rid = _run_id_from(capsys.readouterr().out)
    _record_then_edit("approve")(rid, failing_rename)
    gate.reject(rid, by="Dana", reason="edited after approval")
    last = json.loads(log_path().read_text().splitlines()[-1])
    assert last["supersedes"]["state"] == "approved" and last["supersedes"]["by"] == "Tony"
    assert "changed since the run" in last["verification_error"]


def test_a_recorded_approval_on_a_run_marked_interrupted_can_be_superseded(
    workdir, capsys, failing_rename
):
    """status said approve, approve said interrupted, reject said already recorded: no move."""
    assert main(["run", "Define KPIs and a dashboard"]) == 0
    rid = _run_id_from(capsys.readouterr().out)
    brk, restore = failing_rename
    brk()
    with pytest.raises(OSError):
        gate.approve(rid, by="Tony")
    restore()
    _edit_manifest(rid, lambda m: m.update(status="incomplete"))
    assert _status_json(rid, capsys)["pending_action"] == "reject"
    with pytest.raises(gate.GateError, match="interrupted"):
        gate.approve(rid, by="Tony")
    gate.reject(rid, by="Dana", reason="marked interrupted")
    m = json.loads((_artifact_root() / "rejected" / rid / "manifest.json").read_text())
    assert m["decision"]["supersedes"]["by"] == "Tony"


@pytest.mark.parametrize(
    "edit",
    [{"decision": "x"}, {"decision": {"state": "blocked"}}, {"decisions": "zz"}],
    ids=["decision-string", "decision-unknown-state", "history-string"],
)
def test_a_decided_run_with_edited_history_can_still_be_reopened(workdir, capsys, edit):
    """`status` says done and the page offers reopen; reopen then crashed on the edit."""
    assert main(["run", "Define KPIs and a dashboard"]) == 0
    rid = _run_id_from(capsys.readouterr().out)
    gate.reject(rid, by="Tony", reason="no")
    mf = _artifact_root() / "rejected" / rid / "manifest.json"
    mf.write_text(json.dumps(json.loads(mf.read_text()) | edit))
    assert _status_json(rid, capsys)["pending_action"] == "done"
    gate.reopen(rid, by="Tony", reason="look again")
    m = json.loads((_artifact_root() / "pending" / rid / "manifest.json").read_text())
    key = "decisions" if "decisions" in edit else "decision"
    assert m[f"{key}_malformed"] == edit[key]  # kept, never erased
    assert m["decisions"][-1]["state"] == "reopened"


def test_an_annotation_survives_an_edited_annotation_list(workdir, capsys):
    assert main(["run", "Define KPIs and a dashboard"]) == 0
    rid = _run_id_from(capsys.readouterr().out)
    _edit_manifest(rid, lambda m: m.update(annotations="x"))
    gate.annotate(rid, by="Tony", note="still works")
    m = json.loads((_artifact_root() / "pending" / rid / "manifest.json").read_text())
    assert m["annotations_malformed"] == "x" and m["annotations"][0]["note"] == "still works"


def test_a_deliverable_with_carriage_returns_verifies(workdir, capsys):
    """read_text turned \\r\\n into \\n, so the digest never matched: a false tamper, forever."""
    assert main(["run", "Define KPIs and a dashboard"]) == 0
    rid = _run_id_from(capsys.readouterr().out)
    d = _artifact_root() / "pending" / rid
    from huminloop.governance import review_text

    def edit(m):
        a = _first_file(m)
        text = (d / a["file"]).read_text().replace("\n", "\r\n")
        (d / a["file"]).write_bytes(text.encode("utf-8"))  # content that truly has \r\n
        a.update(sha256=sha256_text(text), review={"ok": review_text(text).ok})

    _edit_manifest(rid, edit)
    s = _status_json(rid, capsys)
    assert s["artifacts_verified"] is True, s["verification_error"]


def test_an_outside_path_is_refused_before_it_is_read(workdir, capsys):
    """A path outside the run must be named as such, never opened and read first."""
    assert main(["run", "Define KPIs and a dashboard"]) == 0
    rid = _run_id_from(capsys.readouterr().out)
    (_artifact_root() / "outside.bin").write_bytes(b"\xff\xfe\x00binary")
    _edit_manifest(rid, lambda m: _first_file(m).update(file="../../outside.bin"))
    s = _status_json(rid, capsys)
    assert s["artifacts_verified"] is False
    assert "outside the run directory" in s["verification_error"], s


def test_a_reject_stores_the_bare_verification_error(workdir, capsys):
    """Text stored inside a successful reject must not say the gate refused to decide."""
    assert main(["run", "Define KPIs and a dashboard"]) == 0
    rid = _run_id_from(capsys.readouterr().out)
    d = _artifact_root() / "pending" / rid
    name = _first_file(json.loads((d / "manifest.json").read_text()))["file"]
    (d / name).write_text((d / name).read_text() + "\nedited\n")
    gate.reject(rid, by="Tony", reason="edited")
    m = json.loads((_artifact_root() / "rejected" / rid / "manifest.json").read_text())
    assert m["decision"]["verification_error"] == f"artifact {name!r} changed since the run"


def test_an_interrupt_during_the_write_does_not_leave_a_claim(workdir, capsys, monkeypatch):
    """Ctrl-C mid-write is BaseException, not Exception; the claim must still be removed."""
    assert main(["run", "Define KPIs and a dashboard"]) == 0
    rid = _run_id_from(capsys.readouterr().out)
    d = _artifact_root() / "pending" / rid

    def interrupted(*a):
        raise KeyboardInterrupt

    real = gate.write_manifest
    monkeypatch.setattr(gate, "write_manifest", interrupted)
    with pytest.raises(KeyboardInterrupt):
        gate.approve(rid, by="Tony")
    assert not (d / gate.DECISION_CLAIM).exists()
    monkeypatch.setattr(gate, "write_manifest", real)
    gate.approve(rid, by="Tony")


# Round 3.


def test_a_windows_text_mode_write_still_verifies(workdir, capsys, monkeypatch):
    """Hashing raw bytes failed every run written in text mode on Windows (\\n became \\r\\n)."""
    import pathlib

    real = pathlib.Path.write_text

    def windows(self, data, encoding=None, errors=None, newline=None):
        if newline is None:
            data, newline = data.replace("\n", "\r\n"), ""
        return real(self, data, encoding=encoding, errors=errors, newline=newline)

    monkeypatch.setattr(pathlib.Path, "write_text", windows)
    assert main(["run", "Define KPIs and a dashboard"]) == 0
    monkeypatch.setattr(pathlib.Path, "write_text", real)
    rid = _run_id_from(capsys.readouterr().out)
    s = _status_json(rid, capsys)
    assert s["artifacts_verified"] is True, s["verification_error"]
    # And the writer, not only the fallback, gets it right: the bytes are the ones hashed.
    d = _artifact_root() / "pending" / rid
    for a in json.loads((d / "manifest.json").read_text())["artifacts"]:
        if a.get("file"):
            assert sha256_text((d / a["file"]).read_bytes().decode("utf-8")) == a["sha256"]


def test_an_autocrlf_checkout_still_verifies(workdir, capsys):
    """Line endings converted after the digest was taken are not a change of content."""
    assert main(["run", "Define KPIs and a dashboard"]) == 0
    rid = _run_id_from(capsys.readouterr().out)
    for f in (_artifact_root() / "pending" / rid).glob("*.md"):
        f.write_bytes(f.read_bytes().replace(b"\n", b"\r\n"))
    s = _status_json(rid, capsys)
    assert s["artifacts_verified"] is True, s["verification_error"]


def test_the_orchestrator_writes_the_bytes_it_hashed(workdir, capsys):
    assert main(["run", "Define KPIs and a dashboard"]) == 0
    rid = _run_id_from(capsys.readouterr().out)
    d = _artifact_root() / "pending" / rid
    for a in json.loads((d / "manifest.json").read_text())["artifacts"]:
        if a.get("file"):
            raw = (d / a["file"]).read_bytes().decode("utf-8")
            assert sha256_text(raw) == a["sha256"], a["file"]


def test_completing_a_recorded_reject_writes_the_set_aside(workdir, capsys, failing_rename):
    """The set-aside happened in memory only, so the decided run kept the bad history."""
    assert main(["run", "Define KPIs and a dashboard"]) == 0
    rid = _run_id_from(capsys.readouterr().out)
    brk, restore = failing_rename
    brk()
    with pytest.raises(OSError):
        gate.reject(rid, by="Tony", reason="first look")
    restore()
    _edit_manifest(rid, lambda m: m["decisions"].append("x"))
    gate.reject(rid, by="Tony", reason="first look")
    m = json.loads((_artifact_root() / "rejected" / rid / "manifest.json").read_text())
    assert m["decisions_malformed"][-1] == "x"
    assert all(isinstance(h, dict) for h in m.get("decisions", []))


def test_reopen_never_supersedes_a_forged_decision(workdir, capsys):
    assert main(["run", "Define KPIs and a dashboard"]) == 0
    rid = _run_id_from(capsys.readouterr().out)
    gate.reject(rid, by="Tony", reason="no")
    mf = _artifact_root() / "rejected" / rid / "manifest.json"
    forged = {"decision": {"state": "blocked", "by": "Mallory"}}
    mf.write_text(json.dumps(json.loads(mf.read_text()) | forged))
    gate.reopen(rid, by="Tony", reason="again")
    m = json.loads((_artifact_root() / "pending" / rid / "manifest.json").read_text())
    assert m["decisions"][-1]["supersedes"] is None


def test_force_on_an_unflagged_run_is_not_recorded_as_forced(workdir, capsys):
    assert main(["run", "Define KPIs and a dashboard"]) == 0
    rid = _run_id_from(capsys.readouterr().out)
    m = gate.approve(rid, by="Tony", note="n", force=True)
    assert m["decision"]["forced"] is False


def test_reject_sets_aside_a_history_with_a_non_mapping(workdir, capsys):
    assert main(["run", "Define KPIs and a dashboard"]) == 0
    rid = _run_id_from(capsys.readouterr().out)
    _edit_manifest(rid, lambda m: m.update(decisions=["x"]))
    gate.reject(rid, by="Tony", reason="edited")
    m = json.loads((_artifact_root() / "rejected" / rid / "manifest.json").read_text())
    assert m["decisions_malformed"] == ["x"]
    assert all(isinstance(h, dict) for h in m["decisions"])


@pytest.mark.parametrize(
    "fields",
    [{"decisions": ["x"]}, {"annotations": 5}, {"annotations": ["x", {"by": "T"}]}],
    ids=["history-entry", "annotations-number", "annotation-entries"],
)
def test_the_terminal_list_and_show_survive_edited_history(workdir, capsys, fields):
    """`pending` crashed for every run on the shapes the web inbox was fixed for."""
    assert main(["run", "Define KPIs and a dashboard"]) == 0
    rid = _run_id_from(capsys.readouterr().out)
    _edit_manifest(rid, lambda m: m.update(fields))
    assert main(["pending"]) == 0 and rid in capsys.readouterr().out
    assert main(["show", rid]) == 0


def test_the_pending_list_does_not_call_a_forged_decision_recorded(workdir, capsys):
    assert main(["run", "Define KPIs and a dashboard"]) == 0
    rid = _run_id_from(capsys.readouterr().out)
    _edit_manifest(rid, lambda m: m.update(decision="x", status="approved"))
    (row,) = [m for m in gate.list_runs("pending") if m["run_id"] == rid]
    assert "decision recorded" not in row["status"]
