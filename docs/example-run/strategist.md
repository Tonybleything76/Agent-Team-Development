Objective:
Build a phased AI transformation roadmap and ROI model for a mid-size manufacturer, sequenced so early phases generate the evidence needed to justify later capital, and tied to a named operating metric rather than a technology purchase.

Body:
**Assumption on scope.** No revenue band, plant count, or current data/analytics maturity was provided. This model assumes `[ASSUMPTION: single-plant, discrete manufacturing, $50–250M revenue, no existing predictive-maintenance or MES-integrated analytics — validate against client's actual revenue, plant count, and system inventory before funding]`.

**Current State (typical for this profile, to be confirmed with client data):**
- Maintenance is largely reactive/preventive on fixed schedules; unplanned downtime is tracked in a CMMS but rarely linked to sensor data.
- Quality inspection is manual/sample-based.
- Planning uses spreadsheets or an ERP module with limited demand-signal integration.
- No formal data governance function; sensor/OT data is siloed from IT.

**Future State:**
- Downtime is predicted from equipment condition data with maintenance triggered by risk score, not calendar.
- Quality defects are caught inline via vision/sensor inspection with human review of flagged items only.
- Planning uses a demand-sensing layer feeding existing ERP, with humans retaining override authority.
- A standing data governance and model-accountability function exists: named owner for data quality, named approver for any model-driven action affecting safety or shipment.

**Roadmap:**

*Phase 0 (Weeks 1–6) — Data Readiness Audit.* Deliverable: inventory of sensor/PLC data availability, historian coverage, CMMS data quality score, and a go/no-go recommendation on which use case has sufficient data to pilot. Cost: audit labor only, no platform spend.

*Phase 1 (Months 2–5) — Bounded Pilot: Predictive Maintenance on 2–3 critical assets.* Deliverable: baseline downtime/cost measured for 60 days pre-pilot, then model deployed and measured for 90 days on the same assets. No plant-wide rollout authorized until this comparison exists.

*Phase 2 (Months 6–9) — Scale Decision + Change Management Build.* Deliverable: revised ROI model using Phase 1 actuals; maintenance team retraining plan; defined escalation path for false positives/negatives; decision on which additional assets or a second use case (quality inspection) get funded.

*Phase 3 (Months 10–18) — Scaled Rollout + Governance Function.* Deliverable: predictive maintenance extended to qualifying assets per Phase 2 data; data governance role formally staffed; model performance reviewed quarterly against baseline.

**ROI Model (formulas shown, figures to be replaced with client data):**

Downtime savings = (Baseline unplanned downtime hours × cost per hour) × predicted reduction %.
Benchmark: predictive maintenance reduces unplanned downtime 20–30% and maintenance costs 10–15% (variance driven by asset criticality mix and existing data quality) [1].

Example using illustrative inputs, not a client prediction:
`[ASSUMPTION: 500 unplanned downtime hrs/yr × $8,000/hr avg cost × 25% reduction = $1.0M gross benefit — every input must be replaced with client CMMS/finance data before this number is cited to the CFO]`

Program cost = Phase 0–1 labor + pilot sensor/platform spend + Phase 2 change management + Phase 3 scale spend. Net ROI = (cumulative benefit − cumulative cost) / cumulative cost, recalculated at end of each phase, not projected once at the start.

Payback period = cumulative cost ÷ (annualized benefit from Phase 1 actuals).

Citations:
[1] Deloitte, "Predictive maintenance and the smart factory," https://www2.deloitte.com/us/en/pages/consulting/articles/predictive-maintenance-smart-factory.html
[2] McKinsey, "Smartening up with Artificial Intelligence" (manufacturing AI value ranges), https://www.mckinsey.com/capabilities/mckinsey-digital/our-insights

Risks:
- **Data quality**: if historian/sensor coverage is thin (common pre-Phase 0 finding), Phase 1 will underperform benchmark and the whole case weakens — this is why Phase 0 exists and must not be skipped.
- **Adoption**: maintenance technicians who don't trust the risk score will override it silently; without a change-management track and a named accountable approver, the model's output is decorative.
- **Sponsorship**: if this roadmap is being requested to justify a platform already purchased, say so now — the sequencing above assumes funding follows evidence, not the reverse.
- **Security/OT exposure**: connecting sensor/PLC data to any cloud analytics layer expands the OT attack surface; this needs its own security review before Phase 1 data flows are built, not after.

Next Steps:
1. Plant operations lead: pull 12 months of CMMS downtime records and historian coverage list by next Friday — feeds Phase 0 directly.
2. IT/OT lead: schedule a security review of any proposed data flow from PLC/sensors to analytics layer before Phase 1 starts.
3. Executive sponsor: name the individual accountable for maintenance-model decisions (override authority) before Phase 1 kicks off.
4. Finance: confirm actual cost-per-downtime-hour and current maintenance spend so the ROI model's assumption placeholders can be replaced with real figures.