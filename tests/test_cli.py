import os

import pytest

from adeptly.cli import main


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
        return "Objective: x\nBody: y\nCitations: none\nRisks: TBD\nNext Steps: z\n"


def test_revise_path_through_cli_blocks_approval(workdir, capsys, monkeypatch):
    import adeptly.cli as cli

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
    from adeptly.cli import load_dotenv

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

    from adeptly.cli import load_dotenv

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
    from adeptly.storage import artifact_root

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
    from adeptly import gate, orchestrator
    from tests.conftest import RecordingLLM

    rec = orchestrator.run("Define KPIs", llm=RecordingLLM())
    gate.reject(rec.run_id, by="Tony", reason="dup")
    assert main(["pending", "--state", "rejected"]) == 0
    assert rec.run_id in capsys.readouterr().out


def test_run_exits_nonzero_when_every_specialist_fails(workdir, capsys, monkeypatch):
    import adeptly.cli as cli

    class DeadLLM:
        name = "dead"

        def generate(self, system, prompt, role=None):
            raise RuntimeError("provider down")

    monkeypatch.setattr(cli, "get_llm", lambda provider=None: DeadLLM())
    assert main(["run", "Define KPIs"]) == 1
    assert "every specialist failed" in capsys.readouterr().err


def test_dotenv_ignores_keys_the_app_does_not_own(workdir, tmp_path, caplog):
    from adeptly.cli import load_dotenv

    env = tmp_path / "hostile.env"
    env.write_text("OPENAI_BASE_URL=http://evil.example\nHTTPS_PROXY=http://evil.example\n")
    with caplog.at_level("WARNING"):
        load_dotenv(env)
    assert "OPENAI_BASE_URL" not in os.environ and "HTTPS_PROXY" not in os.environ
    assert "ignoring unsupported key" in caplog.text


def test_show_strips_terminal_escapes_from_artifacts(workdir, capsys, monkeypatch):
    import adeptly.cli as cli

    class EscapeLLM:
        name = "escape"

        def generate(self, system, prompt, role=None):
            return (
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
