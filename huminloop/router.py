import re
from dataclasses import dataclass, field

from .roles import SPECIALISTS, get_role

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
    # --- Transformation advisors -------------------------------------------------------
    # Vocabulary derived from the ten extraction cases in evals/cases.json (t01-t10) plus each
    # advisor's own remit in roles.py. The five holdout cases (t11-t15) were not read while
    # writing these, which is what makes transformation_route_coverage_holdout a measurement
    # rather than a copy. Ordered by engagement logic, because a task matching two rules
    # dispatches in this order: who owns the outcome, what it is worth, who absorbs the change,
    # how the work is done, then data, architecture, delivery and assurance.
    (
        "domain_ownership",
        (
            "process owner",
            "business owner",
            "end to end",
            "end-to-end",
            "own the outcome",
            "owns the outcome",
            "line of business",
        ),
        ("domain_owner",),
    ),
    (
        "value_realization",
        (
            "business case",
            "value realization",
            "value realisation",
            "benefits realization",
            "benefits realisation",
            "payback",
            "productivity gain",
            "hard savings",
            "pilot",
        ),
        ("value_realization_lead",),
    ),
    (
        "change_adoption",
        (
            "change management",
            "adoption",
            "resistance",
            "organizational readiness",
            "organisational readiness",
            "readiness assessment",
            "go-live",
            "cutover",
            "rollout",
            "sponsorship",
            "executive sponsor",
            "steering committee",
            "role redesign",
            "workforce plan",
            "operating model",
            "line manager",
            "middle manager",
        ),
        ("change_management_lead",),
    ),
    (
        "process_design",
        (
            "process map",
            "process redesign",
            "target state",
            "target-state",
            "future-state process",
            "human in the loop",
            "human-in-the-loop",
            "stay in the loop",
            "stays in the loop",
            "handoff",
            "hand-off",
            "swimlane",
        ),
        ("process_excellence_lead",),
    ),
    (
        "data_readiness",
        (
            "data readiness",
            "data quality",
            "data lineage",
            "data pipeline",
            "training data",
            "fine-tune",
            "fine-tuning",
            "golden dataset",
            "ground truth",
            "labelled data",
            "labeled data",
        ),
        ("data_readiness_lead",),
    ),
    (
        "architecture",
        (
            "target architecture",
            "reference architecture",
            "architecture review",
            "integration blueprint",
            "integration pattern",
            "model selection",
            "model provider",
            "abstraction layer",
            "landing zone",
            "build versus buy",
            "build vs buy",
        ),
        ("enterprise_architect",),
    ),
    (
        "program_delivery",
        (
            "workstream",
            "cross-workstream",
            "sprint",
            "delivery plan",
            "critical path",
            "resource plan",
            "milestone plan",
            "raid log",
            "behind schedule",
        ),
        ("program_management_lead",),
    ),
    (
        "ai_governance",
        (
            "eu ai act",
            "ai act",
            "responsible ai",
            "model risk",
            "bias audit",
            "algorithmic bias",
            "conformity assessment",
            "model card",
            "acceptable use policy",
        ),
        ("governance_advisor",),
    ),
    # --- End transformation advisors ---------------------------------------------------
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

    def staffing(self, task: str, plan: "Plan") -> dict:
        """Why each advisor was staffed, and what would have brought in the ones who were not.

        A reviewer's first question about any team is "who is missing?" — and the honest answer
        here is deterministic, because the router is. Every dispatched role can name the rule and
        the words that summoned it, and every absent one can name the words that would have.
        """
        text = task.lower()
        fired: dict[str, list[str]] = {}
        for name, pattern, rule_roles in self._compiled:
            hit = pattern.search(text)
            if hit:
                for role in rule_roles:
                    fired.setdefault(role, []).append(f"{name} ('{hit.group(0)}')")

        dispatched = [
            {
                "role": role,
                "title": get_role(role).title,
                "why": (
                    "; ".join(fired[role])
                    if role in fired
                    else "no rule matched this task, so the default advisor was staffed"
                ),
            }
            for role in plan.roles
        ]

        would_include: dict[str, list[str]] = {}
        for name, keywords, rule_roles in self.rules:
            for role in rule_roles:
                if role not in plan.roles:
                    sample = ", ".join(f"'{k}'" for k in keywords[:4])
                    would_include.setdefault(role, []).append(f"{name} ({sample})")

        absent = [
            {
                "role": role,
                "title": get_role(role).title,
                "would_join_on": "; ".join(rules),
            }
            for role, rules in sorted(would_include.items())
        ]
        uncovered = sorted(r for r in SPECIALISTS if r not in plan.roles and r not in would_include)
        return {
            "dispatched": dispatched,
            "absent": absent,
            # A specialist no rule can ever reach is a gap in the router, not a judgement call.
            "unreachable": [{"role": r, "title": get_role(r).title} for r in uncovered],
        }

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
