# Example run — synthesis (real provider)

The first committed run to carry a `decision` key: all eight transformation advisors, dispatched
by rule, then read in full and integrated by the Engagement Lead.

- Task: `Our 2,000-person healthcare operations team has finished the claims copilot pilot and the
  steering committee wants to scale it across claims, member services and compliance. Line
  managers are resisting and nobody has mapped where a human stays in the loop end-to-end. Two
  workstreams are behind. Legal is asking whether this falls under the EU AI Act, the claims data
  quality is poor, and we have not settled model selection or the integration blueprint. What do
  we need to decide before go-live?`
- Provider: OpenRouter, `anthropic/claude-sonnet-5`, 2026-09-02
- Plan: all eight transformation advisors, matched by rule (`domain_ownership`,
  `value_realization`, `change_adoption`, `process_design`, `data_readiness`, `architecture`,
  `program_delivery`, `ai_governance`)
- Governance: APPROVE on all nine artifacts, including the synthesis
- Decision: approved by Tony Bleything, `--force` (see `manifest.json` → `decision`) — an
  escalation is a question only a human can answer, and it costs that human their signature

## The first attempt failed, and the fix is also in this repo

The first synthesis call on this exact run came back empty: `finish_reason=length` with no
visible text, after all eight advisors had already succeeded and been paid for. The committed
artifacts here are from a second call — `huminloop resynthesize`, added in v0.12.0 specifically
because this happened — against the same eight artifacts, no advisor re-run. See `CHANGELOG.md`
0.12.0 for the token-budget fix and why a supervisor call needs a larger one than a specialist's.

## What the Engagement Lead is for

Eight advisors is eight memos. Nobody asked "so what do we do." `engagement_lead.md` is the
one deliverable a client actually acts on, and its four registers are the reason it exists:

**Disagreements — the register everything else depends on.** Five of the eight advisors opened
with a near-identical reframe ("scale the copilot" is three decisions bundled as one), which
reads like consensus until you check whether the register underneath it is actually empty. It
isn't:

> Workstream input favoring member services first (lower stakes, cleaner proof of the oversight
> pattern) conflicts with input anchoring on claims as the pilot's natural home. We lean toward
> member services: claims data remediation appears to need 5–10 business days plus governance
> rulings, while the member services gap is a missing task spec, fixable in 1–2 weeks — a faster,
> cleaner first gate. This is a judgment call on timelines, not a settled fact.

That is a synthesis taking a position and naming it as a judgment call rather than hiding it
inside "the team recommends." The second disagreement does the same on whether to hold all three
functions pending EU AI Act classification or let one proceed under proof criteria in parallel.

**Escalations become the gate, not a suggestion.** Seven questions in this run only the sponsor,
Legal, or the client can answer — is there a commercial deadline, does scaling imply headcount
reduction, what's the classification — and each one rides into `process_flags`, which is why
this run needed `--force` and a written note to approve. The mechanism, not just the wording,
is doing the "this is not a rubber stamp" work.

## Layout

`manifest.json` is the record the gate reads: per-artifact governance verdict, the critique
record (points raised, accepted, and why), and the SHA-256 the gate checks against the bytes on
disk before it will let a decision stand. Editing an artifact after the fact makes the digest
disagree and the gate refuses.

- `engagement_lead.md` — the synthesis; start here
- `domain_owner.md`, `value_realization_lead.md`, `change_management_lead.md`,
  `process_excellence_lead.md`, `data_readiness_lead.md`, `enterprise_architect.md`,
  `program_management_lead.md`, `governance_advisor.md` — the eight advisor artifacts it read in
  full to produce that synthesis
