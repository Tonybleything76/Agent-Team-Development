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
    assert "refused" in capsys.readouterr().err


def test_reject_requires_reason_flag(workdir):
    with pytest.raises(SystemExit):
        main(["reject", "abc", "--by", "Tony"])


def test_provider_without_key_fails_clearly(workdir):
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        main(["run", "x", "--provider", "openai"])
