Objective:
Define the KPI tree, baseline sources, decision gates, and human checkpoints needed to know — with evidence, not enthusiasm — whether an AI-driven predictive maintenance program delivers a real return for this manufacturer, and flag where the roadmap currently has no measurement plan behind it.

Body:
**Metric tree** (assumes predictive maintenance on machine-level sensors is the lead use case — must be confirmed with client, not treated as settled):
- **Business outcome**: Unplanned downtime cost avoided ($/yr). Owner: plant controller/finance.
- **Proxy**: Downtime hours avoided per asset class/month — named as a proxy for cost; diverges when severity varies by line. Never report hours as dollars.
- **Instrumented measure**: Failure prediction lead time and work-order close-code accuracy from CMMS (SAP PM/Maximo) and SCADA logs.

**Baseline**: 24 months of CMMS work-order history tagged by failure mode, asset class, downtime duration. Owner: plant maintenance manager; extraction requires IT/ERP admin access. If coding is inconsistent — common in discrete manufacturing — that is a blocking Phase 0 deliverable. [CLIENT DATA REQUIRED]

**Cadence**: instrumented measure weekly during pilot; proxy monthly; business outcome reconciled quarterly against finance's cost-of-downtime figure (needs definition: fully loaded vs marginal labor+scrap).

**Decision gates and accountable owner for each**:
- Phase 0 (data hygiene): [ASSUMPTION: 8 weeks, based on typical CMMS remediation effort for mid-size discrete plants with partial tagging — unvalidated; treat as placeholder, not a committed timeline, until coverage is scanned]. Go only if ≥80% of work orders are coded to a specific failure mode. **Accountable for go/no-go: plant maintenance manager, jointly with the program sponsor.** A miss below 80% may be waived only by the sponsor, in writing, with a stated remediation plan and revised timeline — not silently absorbed into schedule.
- Phase 1 (90-day pilot, one line): Stop if downtime cost reduction is not statistically distinguishable from zero at n = pilot failure events. [ASSUMPTION: <~30 events/asset class/year gives insufficient power for a monthly read — rule-of-thumb, validate with a real power calc once event rates are known.] **Before Phase 1 launches**, a human checkpoint must exist: the maintenance supervisor reviews every model-flagged work order and every technician override weekly, with authority to override the model's recommendation, and each override is logged in the CMMS with a reason code (false alarm, redundant with existing PM schedule, technician judgment). Override rate is tracked as a leading indicator, but the checkpoint — not the metric — is the control. Accountable for the go/no-go call: maintenance manager, informed by this log.
- Phase 2 (scale): Go only if Phase 1 shows a net-positive figure after false-positive labor cost. **This model does not assume maintenance headcount reduction.** If leadership's business case depends on reducing reactive-maintenance headcount as demand for that labor falls, that must be stated explicitly, in those words, and modeled as its own line — how many roles, which shift, redeployment vs. layoff, and who decides — not folded silently into "efficiency" savings. Accountable for the Phase 2 go/no-go: sponsor and finance jointly.

**ROI formula** (not a number — no client figures exist yet): Annual savings = (baseline downtime hrs/yr − pilot downtime hrs/yr) × $/hr downtime [CLIENT DATA — finance] − (false-positive work orders × technician-hrs × loaded rate) − platform/model run cost. External benchmark only, not a target: 10–20% downtime reduction, 5–10% maintenance cost reduction (https://www2.deloitte.com/us/en/pages/energy-and-resources/articles/predictive-maintenance-and-the-smart-factory.html) — do not quote to client before Phase 0 confirms data quality.

Citations:
https://www2.deloitte.com/us/en/pages/energy-and-resources/articles/predictive-maintenance-and-the-smart-factory.html

Risks:
**Data availability** — CMMS coding and sensor coverage unverified; <80% coverage doubles Phase 0. **Attribution** — concurrent capex, staffing changes, and demand swings will confound downtime trends; without a held control line, do not claim attribution. **Sample size** — rare failure events mean early results are likely noise; do not let one good month be reported as proof before the power threshold is met. **Timeline** — the 8-week Phase 0 estimate is a placeholder, not validated against this plant's actual data condition.

Next Steps:
1. Pull 24 months of CMMS work-order history — owner: plant maintenance manager; access granted by IT/ERP admin.
2. Get finance's definition and figure for cost-per-downtime-hour before modeling savings.
3. Run the Phase 0 coverage check and revise the 8-week estimate against actual findings before committing to a Phase 1 budget.
4. Before Phase 1 launch, stand up the override review checkpoint (maintenance supervisor, weekly, logged with reason codes) — do not go live without it.