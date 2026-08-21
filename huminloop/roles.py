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
        "marketing",
        "Marketing",
        Tier.CLIENT_FACING,
        "Research topics, build content calendars, write briefs and campaign outlines.",
    ),
    Role(
        "content_creator",
        "Content Creator",
        Tier.CLIENT_FACING,
        "Draft long-form content and social derivatives; cite sources, state risks and next steps.",
    ),
    Role(
        "social_manager",
        "Social Media Manager",
        Tier.CLIENT_FACING,
        "Schedule posts, threads, UTM tagging, engagement reports.",
    ),
    Role(
        "product_manager",
        "Product Manager",
        Tier.CLIENT_FACING,
        "Write PRDs, stories, prioritize backlog, define acceptance criteria.",
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
        "oem_partner",
        "OEM Partner Leader",
        Tier.CLIENT_FACING,
        "Partner selection, JMF/MDF, co-marketing; pipeline syncs.",
    ),
    # Support specialists: not client-facing, but the team does not function without them.
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
    Role("it", "IT", Tier.SUPPORT, "Provision accounts, backups, monitoring, incident response."),
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
    Role(
        "ea",
        "Executive Assistant",
        Tier.SUPPORT,
        "Agenda packets, follow-ups, travel logistics, meeting summaries.",
    ),
]

ROLES: dict[str, Role] = {r.key: r for r in _ROLE_LIST}
SPECIALISTS: dict[str, Role] = {k: r for k, r in ROLES.items() if r.tier is not Tier.SUPERVISOR}


def get_role(key: str) -> Role:
    try:
        return ROLES[key]
    except KeyError as exc:
        raise KeyError(f"unknown role '{key}'; known: {sorted(ROLES)}") from exc
