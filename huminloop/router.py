import re
from dataclasses import dataclass, field

from .roles import SPECIALISTS

# Each rule: (name, keywords that trigger it, specialists it adds in dispatch order).
# Rules are evaluated in order; every matching rule contributes. Order matters downstream:
# earlier specialists' output is passed as context to later ones. Keywords are matched as
# whole words (optional plural); common single English words are avoided on purpose.
ROUTING_RULES: list[tuple[str, tuple[str, ...], tuple[str, ...]]] = [
    (
        "strategy",
        ("roadmap", "transformation", "strategy", "current state", "future state", "roi"),
        ("strategist", "data_scientist"),
    ),
    (
        "proposal",
        ("rfp", "rfi", "sow", "proposal", "statement of work"),
        ("pre_sales", "legal", "finance"),
    ),
    (
        "sales",
        (
            "leads",
            "lead list",
            "sales lead",
            "email sequence",
            "outreach sequence",
            "follow-up sequence",
            "follow-up email",
            "sales pipeline",
            "pipeline review",
            "discovery call",
        ),
        ("sales",),
    ),
    (
        "product",
        ("prd", "backlog", "user story", "user stories", "acceptance criteria"),
        ("product_manager", "product_developer", "qa_qc"),
    ),
    (
        "build",
        ("poc", "connector", "python script", "automation script", "mcp tool", "prototype"),
        ("product_developer", "qa_qc"),
    ),
    ("analytics", ("kpi", "kpis", "dashboard", "baseline", "a/b"), ("data_scientist",)),
    (
        "security",
        ("threat", "security", "vendor review", "key management"),
        ("cybersecurity",),
    ),
    (
        "privacy",
        (
            "dpia",
            "privacy",
            "data retention",
            "retention schedule",
            "retention policy",
            "consent",
            "gdpr",
            "pii",
            "data map",
        ),
        ("privacy", "legal"),
    ),
    ("legal", ("nda", "msa", "contract", "redline", "clause"), ("legal",)),
    ("people", ("onboard", "onboarding", "sop", "skills matrix", "hiring"), ("hr", "ld")),
    (
        "enablement",
        ("curriculum", "training", "training course", "course design", "enablement"),
        ("ld",),
    ),
    ("finance", ("invoice", "forecast", "pricing", "budget", "month-end"), ("finance",)),
    ("operations", ("capacity", "burn report", "burn rate", "vendor management"), ("operations",)),
]

DEFAULT_ROLES: tuple[str, ...] = ("strategist",)


@dataclass
class Plan:
    task: str
    roles: list[str]
    matched_rules: list[str] = field(default_factory=list)

    @property
    def used_default(self) -> bool:
        return not self.matched_rules


def _compile(keywords: tuple[str, ...]) -> re.Pattern:
    """Whole-word match with an optional plural, so 'nda' never fires on 'agenda'."""
    alt = "|".join(re.escape(k) for k in keywords)
    return re.compile(rf"\b(?:{alt})(?:s|es)?\b")


class Router:
    """Keyword router. Deterministic on purpose: a plan must be explainable and testable."""

    def __init__(self, rules=ROUTING_RULES, default: tuple[str, ...] = DEFAULT_ROLES):
        for name, _, roles in [*rules, ("default", (), default)]:
            unknown = [r for r in roles if r not in SPECIALISTS]
            if unknown:
                raise ValueError(f"rule '{name}' names unknown specialists: {unknown}")
        self.rules = rules
        self._compiled = [(name, _compile(kws), roles) for name, kws, roles in rules]
        self.default = default

    def route(self, task: str) -> Plan:
        text = task.lower()
        roles: list[str] = []
        matched: list[str] = []
        for name, pattern, rule_roles in self._compiled:
            if pattern.search(text):
                matched.append(name)
                for r in rule_roles:
                    if r not in roles:
                        roles.append(r)
        if not roles:
            roles = list(self.default)
        return Plan(task=task, roles=roles, matched_rules=matched)
