import re
from dataclasses import dataclass, field

from .roles import SPECIALISTS

# Each rule: (keywords that trigger it, specialists it adds, in dispatch order).
# Rules are evaluated in order; every matching rule contributes. Order matters
# downstream: earlier specialists' output is passed as context to later ones.
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
        ("lead", "sequence", "follow-up", "follow up", "pipeline", "discovery call"),
        ("sales",),
    ),
    (
        "campaign",
        ("blog", "calendar", "campaign", "content brief"),
        ("marketing", "content_creator", "social_manager"),
    ),
    ("social", ("linkedin", "thread", "social post"), ("social_manager", "content_creator")),
    (
        "product",
        ("prd", "backlog", "user story", "user stories", "acceptance criteria"),
        ("product_manager", "product_developer", "qa_qc"),
    ),
    (
        "build",
        ("poc", "connector", "script", "mcp tool", "prototype"),
        ("product_developer", "qa_qc"),
    ),
    ("analytics", ("kpi", "kpis", "dashboard", "baseline", "a/b"), ("data_scientist",)),
    ("security", ("threat", "security", "vendor review", "key management"), ("cybersecurity",)),
    ("privacy", ("dpia", "privacy", "retention", "consent", "gdpr", "pii"), ("privacy", "legal")),
    ("legal", ("nda", "msa", "contract", "redline"), ("legal",)),
    ("people", ("onboard", "onboarding", "sop", "skills matrix", "hiring"), ("hr", "ld")),
    ("enablement", ("curriculum", "training", "course", "enablement"), ("ld",)),
    ("finance", ("invoice", "forecast", "pricing", "budget", "month-end"), ("finance",)),
    ("operations", ("capacity", "burn", "vendor management"), ("operations",)),
    ("it", ("provision", "provisioning", "backup", "monitoring", "incident"), ("it",)),
    ("partner", ("partner", "oem", "co-marketing", "mdf"), ("oem_partner",)),
    ("admin", ("agenda", "meeting", "travel", "summary"), ("ea",)),
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


def _matches(keyword: str, text: str) -> bool:
    """Whole-word match with an optional plural, so 'nda' never fires on 'agenda'."""
    return re.search(rf"\b{re.escape(keyword)}(s|es)?\b", text) is not None


class Router:
    """Keyword router. Deterministic on purpose: a plan must be explainable and testable."""

    def __init__(self, rules=ROUTING_RULES, default: tuple[str, ...] = DEFAULT_ROLES):
        for name, _, roles in rules:
            unknown = [r for r in roles if r not in SPECIALISTS]
            if unknown:
                raise ValueError(f"rule '{name}' names unknown specialists: {unknown}")
        self.rules = rules
        self.default = default

    def route(self, task: str) -> Plan:
        text = task.lower()
        roles: list[str] = []
        matched: list[str] = []
        for name, keywords, rule_roles in self.rules:
            if any(_matches(k, text) for k in keywords):
                matched.append(name)
                for r in rule_roles:
                    if r not in roles:
                        roles.append(r)
        if not roles:
            roles = list(self.default)
        return Plan(task=task, roles=roles, matched_rules=matched)
