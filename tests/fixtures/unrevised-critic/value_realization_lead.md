Objective:
Decide, on the evidence available, whether the field-copilot pilot has earned a company-wide rollout date — and reconcile the claimed "productivity gain" against a real baseline, a stated denominator, and an honest answer on whether payback assumes headcount reduction. This is not a schedule sign-off.

Body:
**Benefits ledger:**
- *Productivity gain:* **unverified**. No pre-intervention baseline exists; the only data is the pilot's own repair logs, which have known quality issues. It stays out of the ledger until re-measured against a validated pre-copilot baseline.
- *Payback/headcount:* **[ASSUMPTION — unconfirmed]**. If the model reduces technician FTEs, say so in plain words. Even a validated saving is "enabled," not "realized," until someone names the converting decision — work absorbed, a role not backfilled, overtime stopped. Finance owns that call; nobody has made it yet.
- *Denominator:* any hours claim must be checked against the finite pool of technician hours across all initiatives touching this workforce. That reconciliation doesn't exist and is required before any total reaches the committee.

**Scale-or-stop criteria (write before, not after):**
Stop if: validated diagnostic accuracy falls below the safety threshold, the escalation loop isn't live in production, or the AI Act determination comes back high-risk and unmet. Scale only if: the data science lead confirms a realized gain against the clean baseline with a 95% confidence interval, and diagnostic accuracy exceeds 95% agreement with technician-verified ground truth on the golden dataset.

**Who does what, this week:**
- *Executive sponsor* names a single accountable business owner (VP Field Service) by Friday — no rollout planning proceeds without this.
- *Data science lead* pulls 90 days of pre-copilot repair logs as true baseline, builds and validates the golden dataset (4 weeks), and separately commissions a bias/model-risk audit on the training data and model outputs, due in 5 weeks — this is distinct from, and not satisfied by, the legal AI Act opinion below.
- *Technical/architecture lead* (named by the sponsor) delivers a target architecture and model-selection recommendation with trade-offs in 3 weeks; a second named lead delivers the FSM system integration blueprint (data flows, latency, failure modes) in 4 weeks.
- *Workstream lead* for the currently unresourced stream gets a resource plan and named staff within 2 weeks, or that workstream is descoped from the rollout date.
- *Process owner* (named this week) draws the disputed-diagnosis escalation map: who reviews an override, on what evidence, who is accountable when the copilot is wrong — no production date without this tested on paper.
- *Legal/compliance lead* delivers an AI Act high-risk determination within 2 weeks — a legal classification, separate from the technical bias audit above.
- *HR Business Partner* runs structured interviews with resisting technicians and line managers within 2 weeks; findings feed directly into the process owner's escalation-map design, not a standalone report.

Citations:
- EU AI Act, high-risk classification criteria: https://artificialintelligenceact.eu/high-level-summary/
- McKinsey benchmark on GenAI productivity gains (external benchmark only, not client-realized value): https://www.mckinsey.com/capabilities/mckinsey-digital/our-insights/the-economic-potential-of-generative-ai-the-next-productivity-frontier

Risks:
The claim most likely to evaporate under audit is the pilot productivity gain — no baseline, contested data quality. A silent headcount assumption in the payback model, if it exists, must be disclosed before any vote. No accountable owner means no one currently holds authority to stop the program, so schedule pressure — not evidence — is driving the timeline. The missing escalation map and unaudited model are live safety and regulatory exposures, not process nicety. Undecided architecture and an unresourced workstream mean the "milestone plan" being missed was never resourced to hit in the first place.

Next Steps:
Verify the productivity claim first — owned by the data science lead, against the 90-day pre-copilot baseline, reporting into the Field Service Ops monthly review — target 4 weeks. Business owner named this week. Legal AI Act determination and bias audit run in parallel, 2 and 5 weeks respectively. No rollout date is set until scale-or-stop criteria are met, the escalation map exists in tested form, and architecture/integration deliverables above are complete.