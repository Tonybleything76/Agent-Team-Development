import pytest

from adeptly.llm import DryRunLLM, get_llm


def test_default_provider_is_dryrun(workdir):
    assert isinstance(get_llm(), DryRunLLM)


def test_unknown_provider_is_rejected(workdir):
    with pytest.raises(ValueError):
        get_llm("gemini")


def test_anthropic_without_key_fails_clearly(workdir):
    with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
        get_llm("anthropic")


class _Msg:
    def __init__(self, content):
        self.content = content


class _Choice:
    def __init__(self, content):
        self.message = _Msg(content)
        self.finish_reason = "stop"


class FakeOpenAIClient:
    def __init__(self):
        self.calls = []

        class _Completions:
            def create(inner, **kw):
                self.calls.append(kw)
                return type("R", (), {"choices": [_Choice("Objective: via openai")]})()

        self.chat = type("C", (), {"completions": _Completions()})()


def test_openai_client_is_called_with_system_and_user_messages():
    from adeptly.llm import OpenAILLM

    fake = FakeOpenAIClient()
    llm = OpenAILLM(model="test-model", client=fake)
    assert llm.generate("SYS", "USER") == "Objective: via openai"
    kw = fake.calls[0]
    assert kw["model"] == "test-model"
    assert kw["messages"] == [
        {"role": "system", "content": "SYS"},
        {"role": "user", "content": "USER"},
    ]


def test_openrouter_without_key_fails_clearly(workdir):
    with pytest.raises(RuntimeError, match="OPENROUTER_API_KEY"):
        get_llm("openrouter")


def test_openrouter_resolves_model_per_role(workdir, monkeypatch):
    from adeptly.llm import DEFAULT_OPENROUTER_MODEL, OpenRouterLLM

    fake = FakeOpenAIClient()
    llm = OpenRouterLLM(client=fake)
    # No env set: the package default carries every role.
    llm.generate("SYS", "USER", role="strategist")
    assert fake.calls[0]["model"] == DEFAULT_OPENROUTER_MODEL
    # A global override applies to roles without their own model...
    monkeypatch.setenv("OPENROUTER_MODEL", "openai/gpt-5-mini")
    # ...and a per-role override beats the global one for that role only.
    monkeypatch.setenv("OPENROUTER_MODEL_PRE_SALES", "anthropic/claude-opus-5")
    llm.generate("SYS", "USER", role="strategist")
    llm.generate("SYS", "USER", role="pre_sales")
    assert fake.calls[1]["model"] == "openai/gpt-5-mini"
    assert fake.calls[2]["model"] == "anthropic/claude-opus-5"


def test_openrouter_explicit_model_beats_env(workdir, monkeypatch):
    from adeptly.llm import OpenRouterLLM

    monkeypatch.setenv("OPENROUTER_MODEL_PRE_SALES", "anthropic/claude-opus-5")
    fake = FakeOpenAIClient()
    llm = OpenRouterLLM(model="pinned/model", client=fake)
    llm.generate("SYS", "USER", role="pre_sales")
    assert fake.calls[0]["model"] == "pinned/model"


class FakeAnthropicClient:
    def __init__(self):
        self.calls = []

        class _Messages:
            def create(inner, **kw):
                self.calls.append(kw)
                block = type("B", (), {"text": "Objective: via anthropic"})()
                return type("R", (), {"content": [block], "stop_reason": "end_turn"})()

        self.messages = _Messages()


def test_anthropic_client_is_called_with_system_kwarg():
    from adeptly.llm import AnthropicLLM

    fake = FakeAnthropicClient()
    llm = AnthropicLLM(model="test-model", client=fake)
    assert llm.generate("SYS", "USER") == "Objective: via anthropic"
    kw = fake.calls[0]
    assert kw["system"] == "SYS" and kw["messages"][0]["content"] == "USER"


def test_version_is_single_sourced():
    from pathlib import Path

    from adeptly import __version__

    assert (
        Path(__file__).resolve().parents[1].joinpath("VERSION").read_text().strip() == __version__
    )
