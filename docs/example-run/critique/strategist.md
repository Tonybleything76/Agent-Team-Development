Objective:
Build a phased AI transformation roadmap and ROI model for a mid-size discrete manufacturer, sequencing investment by evidence rather than ambition, and naming who does the work differently at each stage.

Body:

**Current State (assumed, pending validation)** — No industry, revenue, or system inventory was provided. [ASSUMPTION: mid-size discrete manufacturer, $150M–$500M revenue, 2–5 plants, ERP + partial machine-level sensors, no unified data layer, maintenance planning largely paper/spreadsheet-driven — basis: modal profile of similar engagements; replace with client data before spend.] Downtime, quality-hold, and scheduling decisions rest today with plant managers and maintenance leads using experience and lagging reports.

**Future State** — Maintenance technicians receive AI risk scores they can inspect and override; quality inspectors get AI-assisted defect flagging that speeds, not replaces, sign-off; plant managers see a unified downtime/quality dashboard. Authority to stop a line or release a held unit stays with the human role.

**Roadmap**

*Phase 0 (Wk 1–6) — Data readiness audit.* IT/OT lead + one plant manager assess sensor coverage, data quality, and history on one line. Deliverable: readiness scorecard, go/no-go on Phase 1. Cost: internal time only.

*Phase 1 (Mo 2–5) — Bounded pilot: predictive maintenance, one line.* Before go-live, maintenance technicians receive a half-day session (taught by vendor applications engineer + shift supervisor) on how risk scores are generated and how to log an override, followed by one week of paired shadow-use. Technicians lose unquestioned latitude over stop/run calls — every override is now logged and reviewed weekly by the maintenance supervisor, which is a real change in standing, not just a paperwork step. Deliverable: baseline vs. pilot downtime, override-log analysis (are overrides well-founded? feed back into the model).

*Phase 2 (Mo 6–9) — Scale + quality-inspection pilot.* Expand only if Phase 1 shows measurable downtime reduction. Quality inspectors trained (2 days classroom + 2 weeks shadow-use, vendor engineer + internal quality lead) on AI-flagged defect review; inspectors retain final sign-off.

*Phase 3 (Mo 10–18) — Enterprise rollout + governance.* Scale proven use cases plant by plant; standing model-risk review board formalized (detail in Next Steps).

**ROI Model**

Downtime savings = (baseline unplanned downtime hrs × downtime reduction %) × (cost-per-hour of downtime, client data).
Benchmark: predictive maintenance cuts unplanned downtime 20–35%, maintenance cost 10–20% (McKinsey — this range spans process and discrete manufacturing; treat as directional for this client, not predictive, until Phase 1 data exists).
Quality savings = baseline scrap/rework cost × defect-catch-rate improvement % (from pilot data).
Investment = Phase 1 pilot cost (sensors, software, integration, training hours) + Phase 2/3 scaling cost — each client-specific, unsourced today.
Payback = cumulative investment ÷ (monthly downtime savings + quality savings) — calculate only after Phase 1 baseline is measured; do not project payback pre-pilot.

Citations:
- https://www.mckinsey.com/capabilities/operations/our-insights/predictive-maintenance-in-manufacturing

Risks:
- No sponsor or budget commitment is confirmed beyond the pilot — do not treat this as funded past Phase 1.
- If this program justifies a vendor platform already selected, say so now — sequencing assumes tool choice is still open.
- OT/cybersecurity exposure: connecting machine-level sensors to a predictive model on live production equipment creates a new attack surface; the OT/security lead must sign off on the connectivity architecture before Phase 1 goes live, not after.
- Data quality: if the Phase 0 audit fails, ROI cannot be estimated reliably — stop or redirect, don't proceed on hope.
- Adoption: technicians whose overrides aren't reviewed and fed back will disengage or route around the tool — the override log is not optional, and neither is naming the standing cost to them upfront.
- Accountability gap: if no one is named accountable when the model is wrong (missed failure, false quality hold), the program stalls at the first incident.
- Headcount: if downtime/quality gains are expected to reduce maintenance or inspection headcount, say so to the sponsor now, not after Phase 2.

Next Steps:
1. Plant manager + IT/OT lead: run Phase 0 data readiness audit on one line (start Monday, 6 weeks).
2. OT/security lead: review and approve sensor connectivity architecture before Phase 1 sensor go-live.
3. CFO/finance partner: supply actual downtime cost-per-hour and scrap/rework spend so the ROI model runs on real figures.
4. Sponsor: name the model-risk accountability owner before Phase 1 begins.
5. Maintenance supervisor: design the technician training session and override-logging process before pilot start.
6. Sponsor: charter the Phase 3 model-risk review board (plant manager, quality lead, maintenance lead, rotating line technician) to meet monthly on override rates, drift, and accountability once Phase 2 begins.