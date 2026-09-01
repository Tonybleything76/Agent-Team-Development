from dataclasses import dataclass
from enum import StrEnum


class Tier(StrEnum):
    SUPERVISOR = "supervisor"
    CLIENT_FACING = "client_facing"
    SUPPORT = "support"


@dataclass(frozen=True)
class Role:
    key: str
    title: str
    tier: Tier
    instruction: str


_ROLE_LIST = [
    # Supervisor tier: these run the loop; they are never dispatched as specialists.
    Role(
        "router",
        "Router / Supervisor",
        Tier.SUPERVISOR,
        "Classify intent, plan, assign agents, schedule governance review, escalate blockers.",
    ),
    Role(
        "governance",
        "Governance Evaluator",
        Tier.SUPERVISOR,
        "Run policy checks, verify citations, PII, tone and accessibility; approve or return.",
    ),
    # Client-facing specialists.
    Role(
        "strategist",
        "Strategist",
        Tier.CLIENT_FACING,
        "Map current to future state, create roadmap and ROI model; align to business goals.",
    ),
    Role(
        "pre_sales",
        "Pre-Sales",
        Tier.CLIENT_FACING,
        "Draft RFP/RFI responses, SOWs, and implementation outlines with assumptions and risks.",
    ),
    Role(
        "sales",
        "Sales",
        Tier.CLIENT_FACING,
        "Capture discovery, generate follow-ups and sequences, update pipeline records.",
    ),
    Role(
        "product_manager",
        "AI Product Manager",
        Tier.CLIENT_FACING,
        "Own the feature backlog and user stories; decide whether an MVP meets the requirements "
        "of the people who must use it. Translate business need into buildable specification.",
    ),
    Role(
        "product_developer",
        "Product Developer",
        Tier.CLIENT_FACING,
        "Build POCs, connectors, scripts, MCP tools, deployment utilities.",
    ),
    Role(
        "data_scientist",
        "Data Scientist",
        Tier.CLIENT_FACING,
        "Define KPIs, run baselines and A/B tests, create dashboards and cost models.",
    ),
    Role(
        "ld",
        "Learning & Development",
        Tier.CLIENT_FACING,
        "Curricula, micro-videos, quick-reference guides, enablement packs.",
    ),
    Role(
        "domain_owner",
        "Domain Owner",
        Tier.CLIENT_FACING,
        "Decide which end-to-end business processes are redesigned and sign off on realized "
        "business value. Own the outcome, not the technology.",
    ),
    Role(
        "value_realization_lead",
        "Value Realization Lead",
        Tier.CLIENT_FACING,
        "Own the business case baseline; decide the ROI and productivity metrics; sign off on "
        "whether a pilot has earned the right to scale.",
    ),
    Role(
        "change_management_lead",
        "Change Management & Adoption Lead",
        Tier.CLIENT_FACING,
        "Own the organizational readiness plan, the training curriculum and the role-redesign "
        "strategy. Hold authority to delay a rollout when readiness assessments say the workforce "
        "is not ready.",
    ),
    Role(
        "process_excellence_lead",
        "Process Excellence Lead",
        Tier.CLIENT_FACING,
        "Own the future-state process map and decide the exact interaction points between people "
        "and AI agents, including where a human must stay in the loop.",
    ),
    Role(
        "data_readiness_lead",
        "Data Readiness Lead",
        Tier.CLIENT_FACING,
        "Own data pipeline readiness; decide which datasets are approved for training or "
        "fine-tuning, and what must be true before modeling spend begins.",
    ),
    Role(
        "enterprise_architect",
        "Enterprise AI Architect",
        Tier.CLIENT_FACING,
        "Decide the technology ecosystem — cloud, model selection, data pipelines — and own the "
        "integration blueprint the delivery team builds against.",
    ),
    Role(
        "program_management_lead",
        "Program Management Lead",
        Tier.CLIENT_FACING,
        "Own sprint execution, resource allocation and cross-workstream coordination; hold the "
        "delivery timeline and escalate what threatens it.",
    ),
    # Support specialists: not client-facing, but the team does not function without them.
    Role(
        "governance_advisor",
        "AI Governance & Risk Advisor",
        Tier.SUPPORT,
        "Own the ethical and regulatory gate: reason about EU AI Act exposure, bias, privacy and "
        "security posture, and say plainly when a system must not ship. Advisory counterpart to "
        "the automated governance evaluator; never rubber-stamps.",
    ),
    Role(
        "cybersecurity",
        "Cybersecurity",
        Tier.SUPPORT,
        "Threat modeling, key management, policy enforcement, vendor review.",
    ),
    Role(
        "privacy",
        "Privacy",
        Tier.SUPPORT,
        "DPIAs, data maps, retention, consent logs; contract data clauses.",
    ),
    Role(
        "legal", "Legal", Tier.SUPPORT, "NDAs/MSAs/SOW redlines, clause library, negotiation notes."
    ),
    Role(
        "finance",
        "Accountant / Finance",
        Tier.SUPPORT,
        "Forecasts, invoices, pricing sheets; month-end close.",
    ),
    Role("hr", "HR", Tier.SUPPORT, "Onboarding, SOPs, skills matrix, training assignments."),
    Role(
        "operations",
        "Operations",
        Tier.SUPPORT,
        "Capacity, burn reports, vendor management, invoicing flow.",
    ),
    Role(
        "qa_qc",
        "QA/QC",
        Tier.SUPPORT,
        "Create test plans, run accessibility and regression checks; record sign-offs.",
    ),
]

ROLES: dict[str, Role] = {r.key: r for r in _ROLE_LIST}
SPECIALISTS: dict[str, Role] = {k: r for k, r in ROLES.items() if r.tier is not Tier.SUPERVISOR}


def get_role(key: str) -> Role:
    try:
        return ROLES[key]
    except KeyError as exc:
        raise KeyError(f"unknown role '{key}'; known: {sorted(ROLES)}") from exc
