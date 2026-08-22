"""Persona loading.

A role's one-line remit is enough to route and to test, but not enough to produce work worth
reviewing. A persona is the rest: how the specialist works, what its output must contain, and
what it must refuse. Personas live as markdown next to the code so they can be edited without
touching Python, and a role without one falls back to its remit.
"""

from functools import cache
from pathlib import Path

PERSONA_DIR = Path(__file__).parent / "personas"
# The house brief goes to every specialist. It carries what the whole team owes regardless of
# role — rigour paired with the human impact of the change — so it lives in one file rather
# than being restated in each persona, where it would drift.
HOUSE_FILE = PERSONA_DIR / "_house.md"


@cache
def load_house_brief() -> str | None:
    if not HOUSE_FILE.is_file():
        return None
    return HOUSE_FILE.read_text(encoding="utf-8").strip() or None


@cache
def load_persona(role_key: str) -> str | None:
    path = PERSONA_DIR / f"{role_key}.md"
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8").strip()
    return text or None


def has_persona(role_key: str) -> bool:
    return load_persona(role_key) is not None


def persona_keys() -> list[str]:
    """Role personas only; files beginning with an underscore are shared briefs, not roles."""
    return sorted(p.stem for p in PERSONA_DIR.glob("*.md") if not p.stem.startswith("_"))
