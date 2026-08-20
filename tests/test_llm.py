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
