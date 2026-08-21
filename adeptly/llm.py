import logging
import os
from typing import Protocol

from .roles import Role

log = logging.getLogger(__name__)

PROVIDER_ENV = "LLM_PROVIDER"
PROVIDERS = ("dryrun", "openrouter", "openai", "anthropic")
DEFAULT_PROVIDER = "dryrun"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
# One key, any vendor's models; per-role overrides pick the right model per task.
DEFAULT_OPENROUTER_MODEL = "anthropic/claude-sonnet-5"
DRYRUN_CITATION = (
    "https://github.com/Tonybleything76/Agent-Team-Development/blob/main/docs/ARCHITECTURE.md"
)

SYSTEM_PREFIX = "You are the "
SYSTEM_TEMPLATE = (
    SYSTEM_PREFIX + "{title} on an AI transformation consulting team. Your remit: {instruction} "
    "Write a client-ready deliverable with exactly these labelled sections, each on its own line: "
    "Objective:, Body:, Citations: (at least one https URL), Risks:, Next Steps:. "
    "Never include personal data such as emails or phone numbers."
)
TASK_PREFIX = "Task: "


class LLMClient(Protocol):
    name: str

    # role is the specialist key for this call; providers that route models
    # per role use it, everyone else ignores it.
    def generate(self, system: str, prompt: str, role: str | None = None) -> str: ...


def build_prompt(role: Role, task: str, context: str) -> tuple[str, str]:
    system = SYSTEM_TEMPLATE.format(title=role.title, instruction=role.instruction)
    prompt = f"{TASK_PREFIX}{task}\n"
    if context:
        prompt += f"\nPrior work from teammates on this task:\n{context}\n"
    return system, prompt


class DryRunLLM:
    """Offline provider. Deterministic output so the whole loop is testable without a key."""

    name = "dryrun"

    def generate(self, system: str, prompt: str, role: str | None = None) -> str:
        role_title = system.removeprefix(SYSTEM_PREFIX).split(" on ", 1)[0]
        task = prompt.removeprefix(TASK_PREFIX).split("\n", 1)[0].strip()
        return (
            f"Objective: {role_title} deliverable for: {task}\n"
            f"Body: [dry-run] {role_title} draft. No model was called; this text is generated "
            f"locally so routing, governance and the approval gate can be exercised end to end.\n"
            f"Citations: {DRYRUN_CITATION}\n"
            f"Risks: Dry-run content is illustrative only and must not be released to a client.\n"
            f"Next Steps: Re-run with LLM_PROVIDER=openrouter (or openai/anthropic) and a real key.\n"
        )


class OpenAILLM:
    name = "openai"

    def __init__(self, model: str | None = None, client=None):
        if client is None:
            try:
                from openai import OpenAI
            except ModuleNotFoundError as exc:
                raise RuntimeError("openai extra not installed: uv sync --extra openai") from exc
            client = OpenAI()
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.client = client

    def generate(self, system: str, prompt: str, role: str | None = None) -> str:
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
            temperature=0.2,
        )
        choice = resp.choices[0]
        if getattr(choice, "finish_reason", None) == "length":
            log.warning("openai response truncated (finish_reason=length)")
        return choice.message.content or ""


class OpenRouterLLM:
    """OpenAI-compatible client pointed at OpenRouter: one key, any vendor's models.

    Model selection is per role: OPENROUTER_MODEL_<ROLE_KEY_UPPERCASED> wins for that
    specialist (e.g. OPENROUTER_MODEL_PRE_SALES), then OPENROUTER_MODEL, then the
    package default. Resolution happens at call time so a long-lived client follows
    env changes in tests and notebooks.
    """

    name = "openrouter"

    def __init__(self, model: str | None = None, client=None):
        if client is None:
            try:
                from openai import OpenAI
            except ModuleNotFoundError as exc:
                raise RuntimeError("openai extra not installed: uv sync --extra openai") from exc
            client = OpenAI(
                base_url=OPENROUTER_BASE_URL,
                api_key=os.environ["OPENROUTER_API_KEY"],
                # Optional OpenRouter attribution headers; harmless if ignored.
                default_headers={"X-Title": "adeptly"},
            )
        self.model = model  # explicit model beats all env resolution
        self.client = client

    def resolve_model(self, role: str | None) -> str:
        if self.model:
            return self.model
        if role:
            per_role = os.getenv(f"OPENROUTER_MODEL_{role.upper()}")
            if per_role:
                return per_role
        return os.getenv("OPENROUTER_MODEL", DEFAULT_OPENROUTER_MODEL)

    def generate(self, system: str, prompt: str, role: str | None = None) -> str:
        model = self.resolve_model(role)
        log.info("openrouter: role=%s model=%s", role or "-", model)
        resp = self.client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
            temperature=0.2,
        )
        choice = resp.choices[0]
        if getattr(choice, "finish_reason", None) == "length":
            log.warning("openrouter response truncated (finish_reason=length)")
        return choice.message.content or ""


class AnthropicLLM:
    name = "anthropic"

    def __init__(self, model: str | None = None, client=None, max_tokens: int = 2000):
        if client is None:
            try:
                from anthropic import Anthropic
            except ModuleNotFoundError as exc:
                raise RuntimeError(
                    "anthropic extra not installed: uv sync --extra anthropic"
                ) from exc
            client = Anthropic()
        self.model = model or os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5")
        self.client = client
        self.max_tokens = max_tokens

    def generate(self, system: str, prompt: str, role: str | None = None) -> str:
        resp = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        if getattr(resp, "stop_reason", None) == "max_tokens":
            log.warning("anthropic response truncated (stop_reason=max_tokens)")
        return "".join(getattr(b, "text", "") for b in resp.content)


def get_llm(provider: str | None = None) -> LLMClient:
    provider = (provider or os.getenv(PROVIDER_ENV, DEFAULT_PROVIDER)).lower()
    if provider == "dryrun":
        return DryRunLLM()
    if provider == "openrouter":
        if not os.getenv("OPENROUTER_API_KEY"):
            raise RuntimeError("LLM_PROVIDER=openrouter but OPENROUTER_API_KEY is not set")
        return OpenRouterLLM()
    if provider == "openai":
        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError("LLM_PROVIDER=openai but OPENAI_API_KEY is not set")
        return OpenAILLM()
    if provider == "anthropic":
        if not os.getenv("ANTHROPIC_API_KEY"):
            raise RuntimeError("LLM_PROVIDER=anthropic but ANTHROPIC_API_KEY is not set")
        return AnthropicLLM()
    raise ValueError(f"unknown LLM_PROVIDER '{provider}' (use one of {', '.join(PROVIDERS)})")
