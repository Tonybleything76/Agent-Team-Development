Objective: Decide which single process opens first for scaled rollout, name its accountable owner, and resolve the blocking dependencies — human-in-loop design, EU AI Act classification, data quality, and ownership — before any go-live commitment; model selection and integration architecture are addressed on a separate, later gate.

Body:
The steering committee is treating "scale the copilot" as one decision. It is three, and they should not be approved together.

**Claims adjudication** (intake → decision → payment/denial): highest current cost — rework, overturns, cycle time — but highest regulatory exposure and confirmed poor data quality. No scaling until data remediation and an end-to-end process owner are named.

**Member services** (inquiry → resolution): lower regulatory stakes, fastest path to instrument human-in-loop cleanly. Candidate to open first, but only to prove the pattern — not to authorize claims by extension.

**Compliance** (review → attestation): a wrong attestation is a regulatory event, not a service miss. Owner must be named before this workstream proceeds at all.

For each: a named individual with authority to change the workflow, whose budget carries the benefit, and who answers for harm. If the committee cannot produce three distinct, empowered names, that is the finding, not a paperwork gap.

**Human-in-loop**: not mapped for any of the three. Go/no-go gate — who reviews, on what evidence, override authority, and how overrides are logged and fed back.

**EU AI Act**: claims decisions affecting eligibility or benefits plausibly fall under Annex III high-risk insurance use cases, triggering mandatory risk management, data governance, and oversight obligations. This needs a legal determination, not a workstream assumption.

**Data quality**: pilot instrumentation cannot certify safety on production claims data known to be poor. Baseline and remediation plan required from claims' own operational reporting before scaling is even considered.

**Model selection and integration blueprint**: deliberately excluded from this gate. Both are technical decisions that should follow, not precede, process and owner selection — deciding the model before deciding who owns the process and what oversight it requires is backwards. Technical lead owns this decision once the first process (member services, pending owner) is confirmed; target: within 4 weeks of owner sign-off, not before.

**Out of scope**: complex claims disputes, appeals, and edge-case compliance reviews stay fully human-handled. Senior adjusters and compliance reviewers carry these today; confirm that stays true after go-live.

**What "proven" means for member services**: before claims work resumes, member services must show — for a minimum 4-week run — override rate and reason logged for every AI-assisted resolution, escalation path exercised at least once with recorded outcome, and zero unresolved override disputes. Absent these, sequencing to claims does not proceed regardless of enthusiasm.

Citations:
- EU AI Act, Annex III high-risk use cases (insurance risk assessment and pricing): https://artificialintelligenceact.eu/annex/3/
- EU AI Act human oversight requirements, Article 14: https://artificialintelligenceact.eu/article/14/

Risks:
- Two workstreams behind schedule and a committee push to scale across three processes at once reads as a decision already made — the tool may be driving process selection, not the reverse.
- No named, empowered owner surfaced yet for any process against the three ownership tests.
- [ASSUMPTION: line manager resistance reflects unresolved ownership] — unconfirmed; treat as hypothesis until managers are asked directly.
- Human-in-loop undesigned end-to-end is a live safety/compliance gap.
- Legal classification under the EU AI Act unresolved for claims; scaling before determination risks a post-launch compliance failure.
- Poor claims data quality means any claims benefit number from the pilot is unverified against production conditions.
- The two behind-schedule workstreams may lack bandwidth to produce real (not nominal) owners in two weeks; a rushed name-only assignment is worse than a delay.

Next Steps:
1. Within one week, I (or the programme lead) interview the resisting line managers directly to confirm or disconfirm the ownership hypothesis before acting on it.
2. Steering committee names one accountable, empowered owner per process against the three tests within two weeks where feasible; if either behind-schedule workstream cannot produce a real owner in that window, it is paused, not defaulted to a placeholder.
3. Legal issues written EU AI Act classification for claims before that workstream proceeds further.
4. Member services opens first, contingent on its owner being named, and only advances to unblock claims once the 4-week proof criteria above are met and reported in the metrics member services already trusts.
5. Technical lead takes model selection and integration blueprint as a separate decision gate, triggered only after member services owner sign-off.