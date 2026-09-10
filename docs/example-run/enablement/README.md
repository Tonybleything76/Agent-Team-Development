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
