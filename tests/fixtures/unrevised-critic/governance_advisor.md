Objective: State the EU AI Act classification, regulatory obligations, and bias/privacy/security posture for the field diagnostic copilot, test whether the claimed human-in-the-loop control is real, and give an explicit shipping position — not to bless the rollout date already in motion.

Body: **Classification (unsettled — my reading, not a ruling).** No one has classified this system, and the prompt itself flags that gap. My reading: this is likely high-risk under Article 6(1) if the equipment it diagnoses is machinery subject to the EU Machinery Regulation (2023/1230) or another Annex I instrument requiring third-party conformity assessment — an AI system acting as a safety component of such equipment is high-risk regardless of Annex III. The advisory-only design (technician confirms, copilot cannot write to equipment state) might otherwise qualify for the narrow-task carve-out in Article 6(3), but that carve-out does not apply where the AI is a safety component. This is a factual question about which equipment lines are in scope, and it belongs to Legal/Product Safety, not to consulting judgment. Until answered, I treat this provisionally as high-risk — the safer assumption given "safety-critical" is in the brief.

**If high-risk, obligations follow immediately:** a documented risk management system (Art 9), data governance covering the training data's known quality issues (Art 10 — this is not a "nice to have," it is a legal gate), technical documentation and logging (Art 12), genuine human oversight design (Art 14), accuracy/robustness/cybersecurity testing (Art 15), and conformity assessment before placing on the market (Art 43). None of these exist yet.

**Human oversight test — fails today.** The teammate record shows disagreement handling is informal, often a silent override, "rarely logged." A control nobody records is not a control; it cannot support an Art 14 claim, and it means we cannot even measure how often technicians correctly overrule the model. Until the escalation/logging process map exists with a named recipient for disputed diagnoses, oversight is nominal.

**Bias — absence is the finding.** No disaggregated performance exists by equipment line, technician tenure, or site. The pilot's aggregate "productivity gain" cannot be evidence of fairness or safety; it is exactly where a subgroup failure would hide. This must be measured before scale, not audited after.

**Privacy.** Repair logs likely tie diagnostic disagreement and override behavior to identifiable technicians. If that data feeds performance management, this is profiling under GDPR and needs a DPIA (Art 35) with a lawful basis stated, not assumed.

**Security.** No integration blueprint to the FSM system exists, so there is no attack surface review of a system with (potential) safety consequences.

**Position: do not ship a company-wide rollout date now.** Conditions, each a gate with a named owner and closing evidence — not soft language to be quoted back as approval:

- **Gate 1 (Legal/Product Safety counsel):** Written AI Act classification memo citing the specific machinery/Annex determination. Nothing below proceeds without this.
- **Gate 2 (Enterprise AI Architect + Process Excellence Lead):** Escalation process map with named recipient, mandatory logging of every override, before pilot expansion.
- **Gate 3 (Data Readiness Lead):** Disaggregated accuracy results by equipment line/site/tenure, measured against a validated golden dataset.
- **Gate 4 (DPO):** DPIA covering technician-level performance data use.
- **Gate 5 (Security/Architect):** Integration security review of the FSM connection.

Citations: EU AI Act Articles 6, 9, 10, 12, 14, 15, 43 — https://artificialintelligenceact.eu/; EU Machinery Regulation (EU) 2023/1230 — https://eur-lex.europa.eu/eli/reg/2023/1230/oj; GDPR Art. 35 DPIA — https://gdpr-info.eu/art-35-gdpr/

Risks: The organization is currently relying on an untested assumption — that "advisory only" exempts it from high-risk obligations — which may be false and is a Legal question, not a technical one. Aggregate productivity gains are being treated as safety/fairness evidence with no subgroup data to support that. The lack of override logging means nobody can currently answer "how often is the technician right when they disagree with the model," which is the single most important safety statistic this system produces.

Next Steps: Gate 1 closes first — General Counsel commissions and returns the AI Act classification memo before any architecture, data, or procurement spend continues. In parallel, Process Excellence Lead drafts the escalation/logging process map (2 weeks) since it blocks Gate 2 regardless of classification outcome.