Objective:
Design and gate an AI-assistant rollout for field technicians and project engineers at a 400-person engineering services firm, using ADKAR to sequence the work and named readiness gates to decide, with evidence, whether go-live in the stated timeframe is warranted.

Body:
**ADKAR position:** Leadership has done Awareness work. I have no evidence yet of Desire, Knowledge, or Ability at the frontline — that requires talking to technicians and engineers directly, not their managers. No training calendar until we know where people are stuck.

**Readiness gates (evidence status today):**
1. *Capability* — Can a sample of techs/engineers complete real tasks with the assistant, unassisted, at or above current error rates? **Unevidenced**, no pilot data exists.
2. *Capacity* — Do supervisors/senior techs have paid time to coach, is crew coverage backfilled? **Unevidenced.** First-line managers absorb this twice and nobody has adjusted their workload.
3. *Support cover* — Field connectivity, IT escalation, staffed champion network before go-live? [ASSUMPTION: field sites have inconsistent connectivity, common in this sector — needs on-site validation.]
4. *Role clarity* — Is it written down who can override the assistant, on what evidence, and who is accountable if a diagnostic or spec recommendation is wrong? **Unevidenced**, non-negotiable for safety-critical field work.

All four gates are currently unevidenced. That is a readiness statement, not an opinion.

**Role-by-role impact:**
- *Field technicians* lose discretion over undocumented "tribal knowledge" fixes — real, currently invisible to any assistant. They gain faster documentation access but risk a surveillance perception if activity logs feed reviews. Must learn a verification protocol (physical inspection before acting on any suggestion) and escalation triggers. Taught by senior-tech champions via ride-along — **but this ride-along duration is only feasible once Gate 2 (Capacity/backfill) is closed; it currently assumes the coverage it hasn't secured.**
- *Project engineers* lose ownership of first-draft calculations; the correct question is who carries liability when they sign off on an AI-assisted number. Must learn to red-team assistant output against code/spec, embedded in existing design-review cadence, taught by senior leads.
- *First-line supervisors/foremen* absorb this twice — own job plus crew's. Need explicit backfill hours and input on escalation design, or the rollout stalls here first.

**Curriculum:** field techs train on-device in field conditions (gloves, noise, poor signal) against rehearsed real incidents; engineers train on red-teaming within existing review workflow. Duration and cost for field-tech training are gated on Capacity approval, not assumed.

**Reinforcement:** 60/90-day refreshers, champion office hours, monthly QA audit sampling AI-assisted decisions. Recommendation, not yet a confirmed firm standard: exclude activity metrics (logins, licence use) as adoption evidence; report the fraction of real tasks completed the new way, on a stated denominator.

Citations:
- Prosci, ADKAR Model overview: https://www.prosci.com/methodology/adkar
- NIST AI Risk Management Framework (human oversight and override design): https://www.nist.gov/itl/ai-risk-management-framework

Risks:
1. If the go-live date was set before this readiness work began, say so now — moving it is cheaper than a failed launch atop three prior transformations this workforce already distrusts.
2. Field technicians are least-ready: safety-critical, no capability evidence, and real risk "override authority" becomes decorative if a tech is blamed for delaying a job by rejecting the assistant. No written protocol exists yet.
3. First-line supervisors carry this change unsupported — no backfill plan exists.
4. All four gates are unevidenced. Proceeding without closing Capability and Role Clarity (both roles) is launching on hope, not evidence.

Next Steps:
1. Change Lead runs structured readiness conversations with 8–10 field technicians (not managers) this week, testing Desire and surfacing cost to them.
2. Ops/Training Lead runs a hands-on Capability pilot: 3–5 techs and 3–5 engineers complete real tasks with the assistant under observation, within 10 days — this generates the missing Capability evidence.
3. Safety/Legal jointly draft, within two weeks, a written override-and-accountability protocol covering both field diagnostics and engineering spec sign-off — closing Role Clarity for both roles before any go-live decision.
4. Ops confirms and costs supervisor/crew backfill hours (Capacity gate) before any training duration is finalized.
5. Sponsor decides go/narrow/slip in two weeks with all four gates' evidence in hand — recommendation follows the evidence, not the calendar.