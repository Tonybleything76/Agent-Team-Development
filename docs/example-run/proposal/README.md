# Example run — proposal workflow (real provider)

The `proposal` route is fully persona-driven: Pre-Sales, Legal and Finance each have a persona,
and each also receives the shared house brief in `huminloop/personas/_house.md`.

- Task: `Draft an RFP response and SOW for an AI readiness engagement at a regional hospital network`
- Provider: OpenRouter, `anthropic/claude-sonnet-5`, 2026-08-22
- Governance: APPROVE on all three artifacts
- Specialists run in order and each sees the previous ones' output as fenced, untrusted context

## What the house brief changed

It asks every specialist to pair technical rigour with the human impact of the change: name who
does something differently, what they lose, who decides when a system and a person disagree,
and to say headcount reduction in those words rather than hiding it in "productivity".

Pre-Sales, unprompted by its own persona:

> Clinical staff lose none of their diagnostic authority during this phase — this is an
> assessment, not a deployment — but department heads spend real time (est. 16 hours over
> 8 weeks) that must be backfilled or explicitly deprioritized elsewhere; the client, not this
> team, owns that trade-off. […] that authority sits with the clinician of record, recorded in
> the governance framework, not decided by this engagement.

Finance, holding a line the house brief sets, and reaching across to another specialist's work:

> If the Pre-Sales workforce-readiness plan later recommends staffing reductions, that must be
> stated as headcount reduction — roles and timing named — not folded into "productivity
> uplift." No such line exists yet; flag for Phase 2 SOW.

That second one is the context chain working: Finance read Pre-Sales' output and applied a
team-wide standard to it. Neither behaviour is in either role's own persona; both come from the
one shared file.
