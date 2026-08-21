import os

import pytest

from adeptly.llm import DryRunLLM


@pytest.fixture(autouse=True)
def isolated_environ(monkeypatch):
    """Give every test its own os.environ copy so dotenv tests cannot leak into siblings."""
    monkeypatch.setattr(os, "environ", dict(os.environ))


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
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_MODEL", raising=False)
    monkeypatch.delenv("OPENROUTER_EFFORT", raising=False)
    return tmp_path


class RecordingLLM:
    """Fake provider: returns governance-clean text, records prompts, can fail on demand."""

    name = "fake"

    def __init__(self, fail_roles=()):
        self.calls: list[tuple[str, str]] = []
        self.roles: list[str | None] = []
        self.fail_roles = set(fail_roles)

    def generate(self, system: str, prompt: str, role: str | None = None) -> str:
        self.calls.append((system, prompt))
        self.roles.append(role)
        if role in self.fail_roles:
            raise RuntimeError(f"simulated failure for {role}")
        return DryRunLLM().generate(system, prompt)


@pytest.fixture
def fake_llm():
    return RecordingLLM()


@pytest.fixture
def failing_rename(monkeypatch):
    """Make os.rename raise once, then restore it — used to test decision recovery."""
    import os as _os

    real = _os.rename

    def _break():
        monkeypatch.setattr(_os, "rename", lambda *a, **k: (_ for _ in ()).throw(OSError("disk")))

    def _restore():
        monkeypatch.setattr(_os, "rename", real)

    return _break, _restore
