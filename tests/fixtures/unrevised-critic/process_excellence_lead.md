Objective: Draw the current- and future-state process for technician-copilot disagreement handling, including a check on joint error, name a human checkpoint at every safety-relevant point, and assign a named-role lead and first action to every unresolved workstream in this rollout — before any date is committed.

Body:
**Current state.** Technician diagnoses using manuals, tribal knowledge, and senior-tech calls, then checks the copilot. Agreement → proceeds. Disagreement → informal call to a supervisor or silent override, rarely logged. This under-logging likely explains part of the pilot's data quality problem: repair logs skew toward agreement, which is the wrong basis for a golden dataset.

**Future-state map.**
1. Copilot returns diagnosis + confidence + evidence trail (never a bare answer).
2. Agreement, high confidence → technician proceeds, logs path. No checkpoint here at volume — but see audit below.
3. **Checkpoint 1** — disagreement/low confidence → named shift lead reviews evidence + technician reasoning, full override authority. SLA target: **[ASSUMPTION: 15 minutes, basis = comparable dispatch-escalation SLAs elsewhere in the business; must be validated against actual pilot disagreement volumes before staffing]**.
4. **Checkpoint 2** — safety-critical class (pressure, electrical, injury exposure) → named qualified engineer, not shift lead, pending Annex III classification below.
5. **Agreement-path audit (new)** — weekly random sample of agreement-path outcomes reviewed by a rotating senior technician, specifically hunting joint error (both copilot and technician wrong). This is the control for the failure mode Checkpoint 1/2 can't see, since neither triggers when both parties agree and are wrong.
6. All outcomes log to FSM + disagreement log — audit trail and golden-dataset seed.

**Handoff table:** Copilot→technician: diagnosis+evidence, real time, failure = acting on an uninterrogable answer. Technician→Checkpoint 1: flag+reasoning, SLA above, failure = disputes fester, feeding resistance already reported. Checkpoint→FSM/log: override+reason code, immediate, failure = no golden-dataset seed, bias repeats.

**Exception classes:** disagreement — owner: named shift lead **[ASSUMPTION: 15–20% disagreement rate, typical of early copilots; validate against pilot logs]**; safety-critical dispute — owner: qualified engineer (not yet named); copilot-offline — owner: IT/ops (not yet named). Check shift-lead post-rollout capacity: routine cases moving to the copilot removes the reps that built their judgment.

**Ownership across the full rollout (first action for each):**
- Value-realization business case, incl. headcount question — Finance business partner (named by CFO): rebuild ROI using actual pilot cycle-time/labor data and an explicit headcount scenario, 2 weeks.
- End-to-end rollout owner — none named; sponsor must name one single accountable owner before any other workstream proceeds. This is the largest blocker on the page.
- Architecture/model selection — Head of Engineering: score 2–3 candidate architectures against safety and integration constraints, 3 weeks.
- FSM integration blueprint — Integration lead: document the data contract (fields, latency, failure behavior) before any build starts.
- Under-resourced workstream — rollout owner + Ops sponsor, once named: identify it by name and staff or formally descope it.
- Technician/manager resistance — Field Ops manager + change lead: structured listening sessions surfacing real objections (deskilling, metrics, trust) before training design.
- Bias audit — Model risk lead: run once disagreement-specific logs are pulled, gated by classification below.
- Annex III classification — Legal/Compliance: written memo comparing this use case against Annex III high-risk criteria, due in 2 weeks, reviewed by rollout owner once named; this gates Checkpoint 2 and the audit scope.

Citations: EU AI Act, Annex III high-risk classification criteria — https://artificialintelligenceact.eu/annex/3/

Risks: No end-to-end rollout owner exists — every other item on this list stalls without one, and that gap should close first. Safety-critical exceptions have no named owner. Checkpoint 1 is decorative if shift leads are measured on copilot-adoption while also overriding it — a conflict of interest, not oversight. Without the agreement-path audit, joint error is invisible by design. A date was set before this map, the business case, or the Annex III classification existed.

Next Steps: In parallel over the next two weeks: (1) walk the disagreement-routing path with 2–3 shift leads against real pilot logs, (2) Legal delivers the Annex III memo, (3) Finance rebuilds the ROI model with headcount scenario stated explicitly, (4) sponsor names the rollout owner. No date is discussed until all four return real answers.