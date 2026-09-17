Objective: Sequence the twelve open workstreams into one critical path with named accountable owners, state which resourcing is confirmed versus assumed, and give the sponsor a decision list — not a rollout date, because the evidence to support one does not yet exist.

Body:

**Critical path and consolidated resource/dependency table** (owner shown on both sides of each dependency; allocations marked confirmed or [ASSUMPTION]):

| # | Item | Owner | First action | Depends on | Date | Allocation |
|---|---|---|---|---|---|---|
|1|Name Domain/Business Owner|Sponsor|Name owner with budget & headcount authority|—|Day 5|[ASSUMPTION: 50%, unconfirmed]|
|2|Architecture + AI Act classification|Domain Owner, AI Architect, Legal|Select target architecture; classify risk tier (safety-critical repair guidance is plausibly high-risk)|1|Day 12|Architect: [ASSUMPTION: 60%, unconfirmed]. Legal: **no owner named** — issue|
|3|Integration blueprint to field service system|Enterprise AI Architect|Draft integration spec against FSM system APIs|1, parallel to 2|Day 12|Same as above, unconfirmed|
|4|Golden dataset scoping|Data Readiness Lead|Define validation criteria against architecture|2|Day 19|**No team staffed** — issue|
|5|Escalation/override process map|Process Excellence Lead|Draw the disputed-diagnosis handoff|2|Day 19|Per own memo, not verified by me|
|6|Value realization re-baseline (state headcount assumption explicitly)|Value Realization Lead|Re-run pilot numbers; disclose whether payback assumes reduced headcount|Parallel; sign-off needs 4|Day 12/19|Per own memo, unverified|
|7|Readiness assessment|Change Management Lead|Assess technician/manager readiness against the process map|5|Day 26|Depends on field-ops director time — unconfirmed|
|8|Bias audit / model risk review|TBD (needs owner)|Run audit against golden dataset and classification|2, 4|Day 33|No owner named — issue|
|9|Rollout date decision|Sponsor|Decide, with evidence|1–8|Earliest Day 35|—|

Item 1 is the single dependency that moves the whole date; everything else is stalled behind it. Slack exists only in items 3 and 6, which can run in parallel.

**Interim control, effective today:** until item 5 is drawn, technician judgment overrides the copilot's diagnosis by default, and every override is logged in the existing repair-log system with technician ID and reason. This is a stopgap, not the designed process — Change Management should not be asked to assess readiness against a control that doesn't yet exist.

**RAID:**
*Issues (now, need a decision today):* no Domain Owner; no Legal/Compliance owner; Data Readiness unstaffed; no bias-audit owner; program already behind the prior milestone plan; technician and line-manager resistance is active now, not hypothetical, and needs a named response owner (Change Management Lead), not a future mitigation.
*Risks (might happen, mitigation + trigger):* field-ops directors may not release technician/manager time for the readiness assessment — mitigation: written capacity confirmation by Day 15, owner Change Management Lead; AI Act high-risk classification could extend timeline by months — mitigation: engage counsel by Day 5, not Day 12.

Citations: https://artificialintelligenceact.eu/high-level-summary/ (high-risk classification criteria relevant to safety-critical guidance systems)

Risks: (1) Every resource allocation above is [ASSUMPTION], none confirmed by a line manager — the plan has no verified capacity anywhere. (2) Legal/Compliance, Data Readiness, and the bias audit have no named owner — three unmitigated single points of failure on the critical path. (3) Setting a rollout date before Day 35 would be reporting green with no evidentiary basis; I will not do that.

Next Steps: (1) Sponsor names Domain Owner — by Day 5, or every downstream date slips day-for-day. (2) Sponsor names a Legal/Compliance lead for AI Act classification — by Day 5. (3) Sponsor confirms Data Readiness staffing (engineer + labeler) and a bias-audit owner — by Day 8, or Day 19/33 milestones are void. (4) Field-ops directors confirm technician/manager time in writing — by Day 15, or Change Management's Day 26 milestone is at risk now. (5) Value Realization Lead states plainly, in writing, whether the payback case assumes headcount reduction — by Day 12, before any further business-case discussion proceeds.