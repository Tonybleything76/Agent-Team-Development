Objective: Determine what must be decided — and what must not proceed — before the claims copilot scales to claims, member services, and compliance: EU AI Act classification, human oversight design, data/bias posture, and technical architecture, so a go-live decision is defensible.

Body: The steering committee is treating this as one system. It is at least three deployments plus an unresolved architecture, and none should be scoped or dated together.

**Classification.** Claims adjudication most plausibly falls under Annex III(5)(c) (insurance risk-assessment/eligibility for essential services) — high-risk. That is my reading, not a ruling; Legal confirms this week. Member services, if purely informational, is likely limited-risk (Art. 50 transparency duty). Compliance is the sharpest flag: if it scores or routes cases affecting employee standing, Annex III(4) (worker evaluation) may apply too. Do not resource these as one workstream.

**Human oversight — tested, not asserted.** Nobody has mapped who reviews, on what evidence, or whether an override is recorded. Line-manager resistance is data: if managers already route around the pilot, the checkpoint doesn't fit how the work happens. Art. 14 requires oversight capable of intervening and stopping the system — not a slide. A real map must also say what managers lose (adjudication discretion they currently exercise informally), what they must newly learn (how to exercise and log a formal override), and who trains them, by when. Skipping that produces the same "asserted, not designed" oversight this memo criticizes.

**Bias.** Claims data quality is poor, and no disaggregated performance evidence exists by plan type, region, or correlated characteristics. Aggregate pilot accuracy is not fairness evidence; the absence of disaggregated results is itself the finding.

**Privacy/security.** Claims data is special-category health data (GDPR Art. 9). A DPIA is required regardless of AI Act status; if claims adjudication is confirmed high-risk, an FRIA (Art. 27) is a separate obligation. I have not seen evidence either has started.

**Architecture.** Model selection and the integration blueprint are still open. Until they're fixed, the human-override path can't be built or tested, and the DPIA/FRIA data-flow sections can't be written. This is a real go-live gate, not a background task — it runs in parallel with the legal and oversight gates, owned by engineering, not by Legal or Compliance.

**Position:** Do not ship any function until the gates below close. This is a hold, not proceed-with-conditions worded as approval.

Citations:
- EU AI Act, Regulation (EU) 2024/1689, Annex III(4)(5)(c), Art. 6, 14, 27, 50: https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689
- GDPR Art. 9 (special category data) and Art. 35 (DPIA): https://gdpr-info.eu/art-9-gdpr/

Risks:
- Classification unconfirmed for all three functions; scaling before that is the largest liability, currently unassessed.
- Oversight is asserted but unmapped; if shipped as-is, override authority is decorative and no one can show, post-incident, who could have stopped it.
- No disaggregated bias evidence exists; "the pilot performed well" is being treated as fairness evidence, which it is not.
- Data quality is known-poor for a health-decision system, compounding an open DPIA/FRIA gap into live exposure.
- Two workstreams are already behind schedule; a "hold" position may not survive steering-committee timeline pressure unless someone — named — has the standing to enforce it. Currently no one does.
- Model selection and integration are undecided; oversight and privacy design cannot be finalized against an unbuilt system.

Next Steps:
1. Legal confirms Annex III status per function this week — owner: Legal counsel; evidence: written memo citing specific provision or reasoned exclusion.
2. HITL map drawn end-to-end for claims first, naming reviewer, evidence seen, override path, override log, what managers lose, what they must learn, and who trains them by when — owner: Process Excellence Lead with named line managers.
3. Disaggregated performance results by affected subgroup, by function, dated — owner: Data Readiness Lead.
4. DPIA (and FRIA if high-risk confirmed) initiated in parallel — owner: Privacy/DPO function.
5. Model selection and integration blueprint finalized, with sign-off that oversight and data-flow requirements are technically implementable — owner: Engineering/Architecture Lead; escalation named for schedule conflicts with gates 1–4.