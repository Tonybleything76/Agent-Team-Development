import pytest

from huminloop.llm import DryRunLLM, get_llm


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
    from huminloop.llm import OpenAILLM

    fake = FakeOpenAIClient()
    llm = OpenAILLM(model="test-model", client=fake)
    assert llm.generate("SYS", "USER").text == "Objective: via openai"
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
    from huminloop.llm import DEFAULT_OPENROUTER_MODEL, OpenRouterLLM

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
    from huminloop.llm import OpenRouterLLM

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
    from huminloop.llm import AnthropicLLM

    fake = FakeAnthropicClient()
    llm = AnthropicLLM(model="test-model", client=fake)
    assert llm.generate("SYS", "USER").text == "Objective: via anthropic"
    kw = fake.calls[0]
    assert kw["system"] == "SYS" and kw["messages"][0]["content"] == "USER"


def test_version_is_single_sourced():
    from pathlib import Path

    from huminloop import __version__

    assert (
        Path(__file__).resolve().parents[1].joinpath("VERSION").read_text().strip() == __version__
    )


def test_openrouter_effort_per_role(workdir, monkeypatch):
    from huminloop.llm import OpenRouterLLM

    fake = FakeOpenAIClient()
    llm = OpenRouterLLM(client=fake)
    llm.generate("SYS", "USER", role="strategist")
    assert "extra_body" not in fake.calls[0]  # no effort set: nothing sent
    monkeypatch.setenv("OPENROUTER_EFFORT", "low")
    monkeypatch.setenv("OPENROUTER_EFFORT_STRATEGIST", "HIGH")
    llm.generate("SYS", "USER", role="strategist")
    llm.generate("SYS", "USER", role="legal")
    assert fake.calls[1]["extra_body"] == {"reasoning": {"effort": "high"}}
    assert fake.calls[2]["extra_body"] == {"reasoning": {"effort": "low"}}
    monkeypatch.setenv("OPENROUTER_EFFORT", "extreme")
    with pytest.raises(ValueError, match="OPENROUTER_EFFORT"):
        llm.generate("SYS", "USER", role="legal")


def test_openrouter_direct_construction_without_key_is_a_clear_error(workdir):
    from huminloop.llm import OpenRouterLLM

    with pytest.raises(RuntimeError, match="OPENROUTER_API_KEY"):
        OpenRouterLLM()


def test_calls_are_bounded_by_timeout_and_max_tokens():
    from huminloop.llm import DEFAULT_MAX_TOKENS, DEFAULT_TIMEOUT_S, OpenAILLM

    fake = FakeOpenAIClient()
    OpenAILLM(model="m", client=fake).generate("SYS", "USER")
    assert fake.calls[0]["max_tokens"] == DEFAULT_MAX_TOKENS
    assert fake.calls[0]["timeout"] == DEFAULT_TIMEOUT_S


def test_bounds_are_configurable_and_validated(workdir, monkeypatch):
    from huminloop.llm import OpenAILLM

    monkeypatch.setenv("LLM_MAX_TOKENS", "42")
    monkeypatch.setenv("LLM_TIMEOUT_S", "7")
    fake = FakeOpenAIClient()
    OpenAILLM(model="m", client=fake).generate("SYS", "USER")
    assert fake.calls[0]["max_tokens"] == 42 and fake.calls[0]["timeout"] == 7.0
    monkeypatch.setenv("LLM_TIMEOUT_S", "soon")
    with pytest.raises(ValueError, match="LLM_TIMEOUT_S"):
        OpenAILLM(model="m", client=FakeOpenAIClient()).generate("SYS", "USER")


def test_truncated_response_warns_and_empty_content_is_an_error(caplog):
    from huminloop.llm import OpenAILLM

    fake = FakeOpenAIClient()
    truncated = _Choice(None)
    truncated.finish_reason = "length"
    fake.chat.completions.create = lambda **kw: type("R", (), {"choices": [truncated]})()
    with caplog.at_level("WARNING"), pytest.raises(RuntimeError, match="empty completion"):
        OpenAILLM(model="m", client=fake).generate("SYS", "USER")
    assert "truncated" in caplog.text


def test_empty_completion_names_the_token_cap_when_truncated():
    """The synthesis failure this guards against: finish_reason=length with NO output text.
    A bare 'empty completion' sends a reviewer looking for a model problem; the cap and how
    to raise it must be in the message itself."""
    from huminloop.llm import OpenAILLM

    fake = FakeOpenAIClient()
    truncated = _Choice(None)
    truncated.finish_reason = "length"
    fake.chat.completions.create = lambda **kw: type("R", (), {"choices": [truncated]})()
    with pytest.raises(RuntimeError, match=r"6000-token budget.*LLM_MAX_TOKENS"):
        OpenAILLM(model="m", client=fake).generate("SYS", "USER")


def test_empty_completion_without_truncation_stays_generic():
    """A provider can return empty content without finish_reason=length (e.g. a content
    filter); that case has no token cap to blame, so the message must not invent one."""
    from huminloop.llm import OpenAILLM

    fake = FakeOpenAIClient()
    fake.chat.completions.create = lambda **kw: type("R", (), {"choices": [_Choice(None)]})()
    with pytest.raises(RuntimeError, match="empty completion") as exc_info:
        OpenAILLM(model="m", client=fake).generate("SYS", "USER")
    assert "token budget" not in str(exc_info.value)


def test_resolve_max_tokens_defaults_by_role_tier(workdir):
    """A specialist gets DEFAULT_MAX_TOKENS; a supervisor (today: only the Engagement Lead
    reaches the model) gets the larger supervisor default, with no env configured."""
    from huminloop.llm import DEFAULT_MAX_TOKENS, DEFAULT_SUPERVISOR_MAX_TOKENS, resolve_max_tokens

    assert resolve_max_tokens(None) == DEFAULT_MAX_TOKENS
    assert resolve_max_tokens("pre_sales") == DEFAULT_MAX_TOKENS
    assert resolve_max_tokens("engagement_lead") == DEFAULT_SUPERVISOR_MAX_TOKENS


def test_resolve_max_tokens_env_overrides_in_priority_order(workdir, monkeypatch):
    from huminloop.llm import resolve_max_tokens

    # Global LLM_MAX_TOKENS overrides the supervisor default too.
    monkeypatch.setenv("LLM_MAX_TOKENS", "9000")
    assert resolve_max_tokens("engagement_lead") == 9000
    # A role-specific override wins over the global one.
    monkeypatch.setenv("LLM_MAX_TOKENS_ENGAGEMENT_LEAD", "20000")
    assert resolve_max_tokens("engagement_lead") == 20000
    assert resolve_max_tokens("pre_sales") == 9000  # unaffected by another role's override


def test_openrouter_synthesis_call_gets_the_supervisor_budget(workdir):
    from huminloop.llm import DEFAULT_SUPERVISOR_MAX_TOKENS, OpenRouterLLM

    fake = FakeOpenAIClient()
    OpenRouterLLM(client=fake).generate("SYS", "USER", role="engagement_lead")
    assert fake.calls[0]["max_tokens"] == DEFAULT_SUPERVISOR_MAX_TOKENS


def test_provider_error_with_no_choices_names_the_upstream_error():
    from huminloop.llm import OpenAILLM

    fake = FakeOpenAIClient()
    fake.chat.completions.create = lambda **kw: type(
        "R", (), {"choices": [], "error": {"message": "upstream 502"}}
    )()
    with pytest.raises(RuntimeError, match="upstream 502"):
        OpenAILLM(model="m", client=fake).generate("SYS", "USER")


def test_blank_model_env_falls_back_to_the_default(workdir, monkeypatch):
    from huminloop.llm import DEFAULT_OPENROUTER_MODEL, OpenRouterLLM

    monkeypatch.setenv("OPENROUTER_MODEL", "")
    llm = OpenRouterLLM(client=FakeOpenAIClient())
    assert llm.resolve_model("strategist") == DEFAULT_OPENROUTER_MODEL


def test_bad_effort_fails_at_construction_not_mid_run(workdir, monkeypatch):
    from huminloop.llm import OpenRouterLLM

    monkeypatch.setenv("OPENROUTER_EFFORT", "extreme")
    with pytest.raises(ValueError, match="OPENROUTER_EFFORT"):
        OpenRouterLLM(client=FakeOpenAIClient())


def test_openrouter_accepts_the_documented_effort_values(workdir, monkeypatch):
    from huminloop.llm import OpenRouterLLM

    llm = OpenRouterLLM(client=FakeOpenAIClient())
    for value in ("none", "minimal", "low", "medium", "high", "max", "xhigh"):
        monkeypatch.setenv("OPENROUTER_EFFORT", value)
        assert llm.resolve_effort(None) == value


def test_persona_is_appended_to_the_system_prompt_when_one_exists():
    from huminloop.llm import build_prompt
    from huminloop.personas import has_persona, load_persona
    from huminloop.roles import get_role

    assert has_persona("strategist")
    system, _ = build_prompt(get_role("strategist"), "task", "")
    assert "Your working brief:" in system
    assert load_persona("strategist") in system
    assert "budget your length" in system  # the house contract still applies


def test_roles_without_a_persona_still_work(tmp_path, monkeypatch):
    """Every real specialist now has a persona (coverage reached 1.0), so this proves the
    no-persona fallback with a synthetic role rather than hardcoding a real one — the last
    version of this test hardcoded "hr" as the example, which broke the moment hr got a
    persona. A synthetic key can never be completed out from under the test."""
    import huminloop.personas as personas
    from huminloop.llm import build_prompt
    from huminloop.roles import Role, Tier

    monkeypatch.setattr(personas, "PERSONA_DIR", tmp_path)
    fake_role = Role("no_persona_fixture", "NO PERSONA FIXTURE", Tier.SUPPORT, "test remit")
    assert not personas.has_persona(fake_role.key)
    system, _ = build_prompt(fake_role, "task", "")
    assert "Your working brief:" not in system and "NO PERSONA FIXTURE" in system


def test_house_brief_reaches_every_specialist_even_without_a_persona(tmp_path, monkeypatch):
    import huminloop.personas as personas
    from huminloop.llm import build_prompt
    from huminloop.personas import load_house_brief
    from huminloop.roles import SPECIALISTS, Role, Tier, get_role

    house = load_house_brief()
    assert house and "techno-social" in house
    for key in SPECIALISTS:
        system, _ = build_prompt(get_role(key), "task", "")
        assert house in system, key

    # A role with no persona still gets the house brief — proved with a synthetic role since
    # every real specialist now has one.
    monkeypatch.setattr(personas, "PERSONA_DIR", tmp_path)
    fake_role = Role("no_persona_fixture_2", "NO PERSONA FIXTURE 2", Tier.SUPPORT, "test remit")
    assert not personas.has_persona(fake_role.key)
    system, _ = build_prompt(fake_role, "task", "")
    assert house in system


def test_house_brief_is_not_mistaken_for_a_role_persona():
    from huminloop.personas import load_persona, persona_keys

    assert "_house" not in persona_keys()
    assert load_persona("_house") is None or "_house" not in persona_keys()
