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
