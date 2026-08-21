import pytest


@pytest.fixture
def workdir(tmp_path, monkeypatch):
    """Point artifact and log output at a temp dir so tests never touch the repo."""
    monkeypatch.setenv("ADEPTLY_ROOT", str(tmp_path))
    monkeypatch.setenv("ARTIFACT_DIR", "out")
    monkeypatch.setenv("LOG_DIR", "logs")
    monkeypatch.setenv("ADEPTLY_ENV_FILE", str(tmp_path / "no-such.env"))  # never read repo .env
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    return tmp_path


class RecordingLLM:
    """Fake provider: returns governance-clean text, records prompts, can fail on demand."""

    name = "fake"

    def __init__(self, fail_roles=()):
        self.calls: list[tuple[str, str]] = []
        self.fail_roles = set(fail_roles)

    def generate(self, system: str, prompt: str) -> str:
        self.calls.append((system, prompt))
        for role in self.fail_roles:
            if role in system:
                raise RuntimeError(f"simulated failure for {role}")
        return (
            "Objective: test\nBody: body\nCitations: https://example.com\n"
            "Risks: some\nNext Steps: more\n"
        )


@pytest.fixture
def fake_llm():
    return RecordingLLM()
