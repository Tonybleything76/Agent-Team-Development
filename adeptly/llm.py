import os
from typing import Protocol

from .roles import Role

PROVIDER_ENV = "LLM_PROVIDER"
DEFAULT_PROVIDER = "dryrun"


class LLMClient(Protocol):
    name: str

    def generate(self, system: str, prompt: str) -> str: ...


class DryRunLLM:
    """Offline provider. Deterministic output so the whole loop is testable without a key."""

    name = "dryrun"

    def generate(self, system: str, prompt: str) -> str:
        role_title = system.split("You are the ", 1)[-1].split(" on ", 1)[0]
        task = prompt.split("Task:", 1)[-1].split("\n", 1)[0].strip()
        return (
            f"Objective: {role_title} deliverable for: {task}\n"
            f"Body: [dry-run] {role_title} draft. No model was called; this text is generated "
            f"locally so the routing, governance and approval gate can be exercised end to end.\n"
            f"Citations: https://modelcontextprotocol.io/docs/getting-started/intro\n"
            f"Risks: Dry-run content is illustrative only and must not be released to a client.\n"
            f"Next Steps: Re-run with LLM_PROVIDER=openai or anthropic and a real key.\n"
        )


class OpenAILLM:
    name = "openai"

    def __init__(self, model: str | None = None):
        from openai import OpenAI  # optional dependency, imported lazily

        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.client = OpenAI()

    def generate(self, system: str, prompt: str) -> str:
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
            temperature=0.2,
        )
        return resp.choices[0].message.content or ""


class AnthropicLLM:
    name = "anthropic"

    def __init__(self, model: str | None = None):
        from anthropic import Anthropic  # optional dependency, imported lazily

        self.model = model or os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5")
        self.client = Anthropic()

    def generate(self, system: str, prompt: str) -> str:
        resp = self.client.messages.create(
            model=self.model,
            max_tokens=1500,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(getattr(b, "text", "") for b in resp.content)


def get_llm(provider: str | None = None) -> LLMClient:
    provider = (provider or os.getenv(PROVIDER_ENV, DEFAULT_PROVIDER)).lower()
    if provider == "dryrun":
        return DryRunLLM()
    if provider == "openai":
        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError("LLM_PROVIDER=openai but OPENAI_API_KEY is not set")
        return OpenAILLM()
    if provider == "anthropic":
        if not os.getenv("ANTHROPIC_API_KEY"):
            raise RuntimeError("LLM_PROVIDER=anthropic but ANTHROPIC_API_KEY is not set")
        return AnthropicLLM()
    raise ValueError(f"unknown LLM_PROVIDER '{provider}' (use dryrun, openai, anthropic)")


SYSTEM_TEMPLATE = (
    "You are the {title} on an AI transformation consulting team. Your remit: {instruction} "
    "Write a client-ready deliverable with exactly these labelled sections, each on its own line: "
    "Objective:, Body:, Citations: (at least one https URL), Risks:, Next Steps:. "
    "Never include personal data such as emails or phone numbers."
)


def build_prompt(role: Role, task: str, context: str) -> tuple[str, str]:
    system = SYSTEM_TEMPLATE.format(title=role.title, instruction=role.instruction)
    prompt = f"Task: {task}\n"
    if context:
        prompt += f"\nPrior work from teammates on this task:\n{context}\n"
    return system, prompt
