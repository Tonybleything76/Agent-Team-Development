Objective: Decide the human checkpoints, agent handoffs, and exception routes for the claims adjudication path — the pilot's home ground — before treating "scale to three functions" as one go-live decision; member services and compliance get the same treatment on their own timeline.

Body:
"Scale the copilot" is three decisions bundled as one, and HITL mapping plus EU AI Act classification are gates, not parallel tracks. Legal must confirm Annex III status (claims adjudication affects access to insurance — plausibly high-risk) this week; until confirmed, we design Article 14 human-oversight controls as if high-risk applies by default, because retrofitting oversight after a "not high-risk" call proves wrong is far costlier than over-designing now.

Two other decisions are explicitly out of scope for this document but block go-live regardless: **model selection** (owner: TBD — needs naming, target decision date before integration work starts) and **integration blueprint** (owner: TBD — same). Naming these owners is itself a next step below; shipping this map without them is progress on the wrong critical path.

**Current state, as actually worked (claims):** adjudicator pulls claim, checks policy terms, calls the copilot, and — per line managers to be interviewed directly — frequently overrides using a private eligibility exceptions spreadsheet compliance doesn't know exists. That spreadsheet is where tribal knowledge lives; automating around it without capturing it first automates a fiction.

**Future-state checkpoints (claims), by consequence:**
- *Denial recommendation → adjudicator review.* Consequence: irreversible member harm. Reviewer sees claim, policy clause, copilot reasoning, confidence, and surfaced spreadsheet logic. Full override authority, logged with reason code, compliance-reviewed monthly. Real only if adjudicators retain enough non-automated volume to keep judgment — mitigate via rotation onto complex cases, not removal from queue.
- *Approval, low-value, clean data.* Low, reversible consequence — sampled post-payment audit, not per-case review. Sample rate [ASSUMPTION: 5%, basis: current audit team capacity, to validate]. **Trigger:** if sampled error rate exceeds 3% [ASSUMPTION, to be set with compliance], per-case checkpoint reinstates immediately for that claim category until root cause is fixed.
- *Data-quality flag.* Route to data steward, 48hr SLA, escalates to claims ops lead if unresolved. Volume unknown given known poor data quality — [ASSUMPTION: needs pull from claims intake system before staffing this].

**Exception owners:** disputed medical necessity → clinical reviewer; suspected fraud → compliance, defined SLA; repeat overturn on same clause → policy team (signals model or policy is wrong).

**Adjudicators and the spreadsheet:** anyone who built or ran undocumented override logic is not exposed to compliance action for disclosing it. Owner: claims ops lead, two-week window, formally interviews and captures that logic into the documented exception rules before go-live — it is real operational knowledge, not a violation.

**Handoff contract:** copilot → adjudicator: structured recommendation, reasoning, confidence, delivered in seconds; SLA to act 24hrs; if unactioned, auto-escalate, never auto-approve.

Member services (lower consequence, higher volume, fewer checkpoints) and compliance (higher consequence, feeds regulatory reporting) have not had this exercise. The two workstreams already reported as "behind" are not named in the brief — before confirming claims-first sequencing doesn't stall on them, someone must identify which two and whether they gate this timeline.

Citations: EU AI Act, Annex III high-risk categories including access to essential private/public services and insurance: https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32024R1689

Risks:
- Denial-review checkpoint becomes a rubber stamp if clean-case volume grows and adjudicators lose practice — likely given poor claims data quality inflating the "automatable" bucket.
- Data-quality remediation is unscoped; if exception volume exceeds current staffing, the 48hr SLA fails on day one.
- Compliance's fraud-exception path has no confirmed owner yet — highest-consequence gap; should block compliance go-live specifically.
- Model selection and integration blueprint remain undecided with no named owner — integration risk compounds if chosen after HITL design is finalized.
- The two "behind" workstreams are unnamed; if either touches claims data pipelines or compliance reporting, claims-first sequencing may be optimistic.
- Line manager resistance is signal, not noise, and should be treated as such in planning, not managed away with messaging.

Next Steps: This month — walk the claims adjudication path with claims ops leads, one compliance reviewer, and the adjudicators who ran the exceptions spreadsheet, using real system volumes to size exception queues before setting SLAs. In parallel, get Legal's written Annex III determination, and get the steering committee to name owners and dates for model selection and integration blueprint. Do not schedule member services or compliance mapping until claims checkpoints are validated against one week of live volume, and do not confirm claims-first sequencing until the two behind workstreams are named and checked against it.