# Example run — AI enablement programme (real provider)

The clearest evidence so far that the critique round changes the deliverable rather than
decorating it. Committed unapproved, in `pending/`, because the human decision belongs to a
human and this run has not had one.

- Task: `Design an AI enablement and adoption program for a 400-person engineering services firm
  introducing AI assistants to field technicians and project engineers`
- Provider: OpenRouter, `anthropic/claude-sonnet-5`, 2026-09-09
- Plan: `['change_management_lead', 'ld']`, matched by the `change_adoption` and `enablement` rules
- Engagement Lead synthesis: 5 open decisions, 0 disagreements, 3 items escalated to the human
- Critique: 13 findings across three drafts, 13 accepted, all three artifacts revised
- `run.html` is the rendered narrative report; `manifest.json` carries the full critique record
- `gate-walkthrough.html` / `.txt` — a captured terminal session taking this run through the
  gate, and the clearest single artifact in the repo

## The gate refuses to release this run

The Engagement Lead escalated three questions it says only a human can answer: whether the
go-live date was fixed by a commitment nobody has disclosed, whether there is real budget to pay
supervisors for backfill or whether "free" coaching time is baked into how crews are staffed,
and the fact that no Safety/Legal, IT/Security or Ops seat produced an artifact even though the
override protocol depends on them.

Every artifact passed governance on its own content. An unanswered escalation still flags the
run, so `approve` is refused. Overriding is permitted — sometimes the right call is to proceed
and carry the question — but it costs a name and a written reason and lands in the record as
`forced`. The walkthrough shows the refusal, the override, a reservation recorded with
`annotate` without rejecting, and `reopen` superseding the approval when the reservation turns
out to matter. The history reads approved → reopened → rejected, with who and why at each step.

The operator in that recording is labelled "Demo Operator" because it is a demonstration in a
throwaway directory. It is not a decision Tony made, and the committed run itself remains
undecided in `pending/`.

## What the critics caught

**A citation that did not support its claim.** The Change Management Lead cited
`osha.gov/human-factors` behind an override-and-accountability design. Its critic challenged the
link as not supporting the claim, and the author replaced it with NIST's AI Risk Management
Framework, which does. Specialists have no tool access, so every citation they produce is
recalled rather than retrieved — this is the failure mode most likely to embarrass someone in
front of a client, caught by a peer rather than by the human.

**An assumption about a tool nobody had confirmed.** L&D wrote an objective around the assistant
exposing a confidence score to the technician. Challenged on evidence, the author did not
quietly soften the objective; it became a named risk with an owner, Product/Platform Lead, to
confirm what the tool actually exposes.

**A synthesis made to show its sources.** The Engagement Lead's central claim — that every
readiness gate is unevidenced rather than merely undocumented — was challenged as unattributed.
It now names the two source memos it drew from.

Two more show the house brief's human-impact standard holding: an exercise that assumed every
technician had overridden a SCADA alarm was widened to any automated system or colleague's
judgement call, and a two-week paid ride-along was made explicitly contingent on the backfill
approval rather than assuming crews absorb the loss.

## The caveat that has not gone away

Thirteen findings, thirteen accepted, no pushback — the same pattern as the first critique run,
where it was nine of nine. Either the critiques are consistently right, which the specificity
here supports, or the authors defer by default. `huminloop stats` flags total agreement for
exactly this reason. A critic nobody ever argues with is still only half tested.
