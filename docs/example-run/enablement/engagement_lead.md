Objective:
Give the steering committee a single, actionable readiness call on the AI-assistant rollout to field technicians and project engineers: what to decide, who decides it, where the specialist memos actually agree or don't, and what only the client can answer before Thursday.

Body:

## Recommendation
Do not schedule go-live. The Change Management Lead memo and the L&D curriculum memo independently reached the same conclusion from different angles: every readiness gate that matters for a safety-adjacent rollout — Capability, Capacity, Support cover, Role clarity — is currently unevidenced, not merely undocumented. Those two memos are referenced here, not reproduced; this document is the Engagement Lead's synthesis of them, and the client should read the underlying artifacts before treating the convergence as settled. L&D's curriculum is a sound pilot design but is explicitly contingent on gates it doesn't control. The sentence that survives if the rest of this is lost: close the four readiness gates with real pilot evidence before setting a training calendar — right now you'd be scheduling against unobserved tool behavior and unobserved workforce reaction.

## Decisions
1. Do we hold the go-live date, or slip it pending gate evidence, given contractual or client commitments the team cannot see? -> Sponsor
2. Who is accountable when the assistant's recommendation is wrong — technician, engineer, or firm? -> Safety/Legal (not yet engaged — see Escalations)
3. Does the vendor's tool expose an interpretable, calibrated confidence score, as the curriculum's Objective 1 assumes? -> Product/Platform Lead
4. Will supervisors get paid, costed backfill hours for coaching, or does this land as unpaid extra work? -> Ops Lead. Note: Ops has not been consulted on this engagement to date; treat any timeline estimate as a first-contact briefing, not a fast turnaround.
5. Who co-trains cohort two onward, since only session one has a confirmed instructor? -> L&D / Ops jointly

## Disagreements
None substantive between the two memos — they converge on the same evidence gaps from opposite directions and L&D subordinates its schedule to Change Management's gates. Worth naming: both artifacts wear black and white hats throughout. Nobody argued the yellow-hat case for moving faster. That absence is informative — either the case for speed doesn't exist, or nobody was asked to make it.

## Escalations
1. Was the go-live date set before this readiness work began — is there a contractual commitment driving it? Neither memo can answer this; only the sponsor knows.
2. Is there budget/authority to pay supervisors for backfill hours, or is "free" coaching time structurally assumed in crew staffing? This determines whether Gate 2 can ever close.
3. No Safety/Legal, IT/Security, or Ops seat produced an artifact for this engagement, and Ops is being pulled in for the first time via Decision #4 above. Override-accountability and connectivity validation depend on functions not yet represented — name owners before the next round.

Citations:
- Prosci, ADKAR Model: https://www.prosci.com/methodology/adkar
- NIST AI Risk Management Framework (human oversight and override design): https://www.nist.gov/itl/ai-risk-management-framework
- Guo et al., "On Calibration of Modern Neural Networks" (why confidence scores may be miscalibrated — relevant to Decision #3, unverified for this vendor): https://arxiv.org/abs/1706.04599

Risks:
1. If the go-live date predates this readiness work, moving it now is far cheaper than a failed launch — flagged by Change Management, unresolved.
2. Field technicians are the least-ready group for a safety-critical rollout: no capability evidence, no written override protocol, real risk "authority to override" becomes decorative if a tech is blamed for a delay.
3. This document rests on a synthesis of two memos not included verbatim; if either memo's evidence is weaker than characterized here, the "unevidenced not undocumented" claim needs re-checking against source.
4. The curriculum's core objective assumes unverified vendor confidence-score calibration; if wrong, Objective 1 collapses mid-pilot.
5. Only one cohort has a confirmed instructor; no named co-trainer means the program cannot scale past session one.
6. Supervisors absorb this change twice (job plus coaching) with no confirmed backfill — likely first stall point.

Next Steps:
1. Change Lead runs frontline readiness interviews (8–10 technicians, not managers) this week to test Desire.
2. Ops/Training Lead runs the Capability pilot (3–5 techs, 3–5 engineers) within 10 days, with task scope restricted to non-consequential, reversible decisions until Step 3 is complete.
3. Safety/Legal — currently unnamed — is assigned to draft the override-and-accountability protocol within two weeks; pilot scope expands only after this protocol exists.
4. Product/Platform Lead confirms actual confidence-score behavior before Objective 1 is locked.
5. Sponsor makes the go/narrow/slip call in two weeks once all four gates carry real evidence — recommendation follows evidence, not calendar.