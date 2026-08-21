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

    def generate(self, system, prompt):
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
    env.write_text("# comment\nFOO_FROM_FILE=abc   # inline\nBAR='quoted # kept'\nPRESET=file\n")
    monkeypatch.setenv("PRESET", "env")
    monkeypatch.delenv("FOO_FROM_FILE", raising=False)
    load_dotenv(env)
    import os

    assert os.environ["FOO_FROM_FILE"] == "abc" and os.environ["BAR"] == "quoted # kept"
    assert os.environ["PRESET"] == "env"


def test_root_flag_relocates_output(workdir, tmp_path, capsys, monkeypatch):
    monkeypatch.delenv("ARTIFACT_DIR")
    monkeypatch.delenv("LOG_DIR")
    other = tmp_path / "elsewhere"
    assert main(["--root", str(other), "run", "Define KPIs"]) == 0
    assert (other / "out" / "pending").exists() and (other / "logs" / "runs.jsonl").exists()


def test_env_example_loads_and_runs_dry(workdir, tmp_path, capsys):
    from pathlib import Path

    example = Path(__file__).resolve().parents[1] / ".env.example"
    assert main(["--env-file", str(example), "run", "Define KPIs"]) == 0
    assert "provider: dryrun" in capsys.readouterr().out


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
    env.write_text('export EXP_KEY=abc\nQ_KEY="sk-abc" # prod key\n')
    monkeypatch.delenv("EXP_KEY", raising=False)
    monkeypatch.delenv("Q_KEY", raising=False)
    load_dotenv(env)
    assert os.environ["EXP_KEY"] == "abc" and os.environ["Q_KEY"] == "sk-abc"


def test_env_file_pointing_at_directory_is_one_line(workdir, tmp_path, capsys):
    assert main(["--env-file", str(tmp_path), "roles"]) == 2
    assert capsys.readouterr().err.startswith("error: ")
