Objective: Decide whether the claims copilot pilot has earned scale rights, and gate any go-live on five unresolved items — a verified benefits baseline, an end-to-end human-in-the-loop map, an EU AI Act classification, a data-quality remediation plan, and a settled model-selection/integration blueprint — before committing capacity to claims, member services, and compliance simultaneously.

Body:
"Scale the copilot" is at least three separate decisions bundled into one ask, and two of the open items — human-in-loop design and legal classification — are gates, not workstreams that can run in parallel with rollout. I have not been given a benefits ledger, so nothing in this program is certified yet.

**Ledger, current state:**
- *Claims cycle-time/rework reduction* — **unverified**. Measured, if at all, on the pilot's own instrumentation with no confirmed pre-intervention baseline. Not booked until validated against an independent baseline.
- *FTE hours freed in claims* — **enabled, not realized**. Freed hours aren't money until someone names the conversion decision — role not backfilled, overtime stopped, shift not filled. Not yet named.
- *Member services and compliance benefits* — **projected [ASSUMPTION]**. Neither function ran the pilot; any dollar figure here is extrapolation, not measurement.
- *Data quality effect* — poor claims data means accuracy/cycle-time gains may be partly an artifact of concurrent data cleanup, not the copilot. Must be disentangled before trusting the number.
- *Model selection and integration blueprint* — **undecided**. This isn't a benefit line, it's a blocking dependency: scaling before architecture and model choice are settled risks locking in rework costs and an unowned technical debt line. No go-live date should be set until this has an accountable owner and a decision date.

**Denominator check:** test the portfolio total against actual per-function headcount/hours in claims, member services, and compliance — not the 2,000-person org figure. Without those FTE counts, the same claims-processor hours could be double-counted across claims efficiency and member-services capacity.

**Scale/stop criteria:** were these written before the pilot started? If not, whatever result comes back will look sufficient by construction. I need pre-committed criteria in writing before I can certify a scale decision rather than a preference.

**Human-in-loop and legal:** line manager resistance and the two behind-schedule workstreams are signals, not noise — they may indicate the human checkpoint is undefined, the workload assumptions were wrong, or the tooling isn't ready. That needs direct investigation, not just folding managers into sign-off after the fact. Separately, claims adjudication affecting payment/denial plausibly falls under EU AI Act Annex III high-risk use; classification changes documentation and conformity obligations before go-live.

**Recommendation:** stage the gate. No portfolio-wide rollout. If claims adjudication clears data-quality remediation, a written human-in-loop map, legal classification, and a settled model/integration decision, it earns a bounded second phase with pre-set stop/scale criteria — nothing more, yet.

Citations:
- EU AI Act, Regulation (EU) 2024/1689, Annex III high-risk classification: https://eur-lex.europa.eu/eli/reg/2024/1689/oj
- McKinsey, on AI pilot ROI claims frequently failing under independent measurement: https://www.mckinsey.com/capabilities/quantumblack/our-insights/the-state-of-ai

Risks:
- Highest-likelihood-to-evaporate claim: cycle-time/rework numbers, resting on pilot-owned instrumentation and unconfirmed baseline against poor-quality data.
- Portfolio over-promise: member services and compliance benefits are assumption-only; summed with claims, the total likely exceeds deliverable capacity even in the best case.
- Legal exposure: proceeding before EU AI Act classification risks retroactive conformity failure, not a paperwork delay.
- Decorative oversight: a human-in-loop map written after approval, rather than before, won't survive audit or incident review.
- Unaddressed signal: manager resistance and workstream delays may indicate deeper feasibility problems being treated as scheduling noise.

Next Steps:
1. Claims Ops Director first confirms the pre-pilot weekly report has clean, comparable baseline fields (cycle time, rework, cost/claim); only then commits to a delivery date for the verified baseline — this is the first claim to check.
2. Legal/Compliance lead issues written EU AI Act classification memo before go-live scheduling.
3. Program lead interviews the two behind-schedule workstream owners and a sample of resistant line managers to identify the specific feasibility or workload issue, reporting findings to steering committee within two weeks.
4. Technical lead owns and dates a model-selection/integration blueprint decision before any go-live date is set.
5. Steering committee approves written scale/stop/extend criteria for claims-only phase before phase-two funding discussion.