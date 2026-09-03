# TODOS

## Phase 4 — the paid proof run

**Status: DONE.** Spent, reviewed, approved, and committed as evidence — then spent several more
times to build and shake out the run renderer.

The healthcare claims-copilot task (unchanged since v0.9.0) has now run against the live
OpenRouter provider at least five times. The first, `20260902_044655_a29747`, is the one that
matters for the record: all eight advisors plus the Engagement Lead completed (~$0.80), Tony
reviewed the voice and the synthesis, approved it with `huminloop approve ... --force --note
"..."` (forced because 7 escalation-derived process flags require a note), and it's committed at
`docs/example-run/synthesis/` as the first synthesis example with a `decision` key.

That first run also surfaced a real bug: `parse_registers`'s Escalations capture ran past its own
register boundary into Citations/Risks/Next Steps, so the manifest recorded 7 escalations where
the artifact text only ever supported 3. Fixed in v0.13.0; the committed example's manifest,
approval note, and process flags were corrected to match (the artifact text itself was never
wrong).

Four further runs (`proof3`–`proof5` under this job's tmp dir, local scratch only — not
committed) exercised the full 9-role plan (all eight advisors + `ld`), used to build and verify
`huminloop render` against real output rather than a hand-authored mock. One of those runs is
what caught the Escalations bug above.

**Reference for anyone re-running it:** `LLM_PROVIDER=dryrun uv run huminloop run "<task>"` still
verifies routing/plan shape for free before spending on the live provider.


## Re-resolve the citation URLs in docs/ROSTER-EVIDENCE.md

**Status: DONE (2026-09-02).** All 47 Vertex AI Search redirects replaced with the canonical
publisher URL each one resolves to, verified live (bcg.com, mckinsey.com, medium.com, and
researchgate.net block plain automated fetches — those four were confirmed live by other means,
noted in the doc's header rather than treated as broken). Four Accenture citations [17, 18, 21,
26] resolved to generic careers-search pages rather than the original specific job posting —
correctly attributed, just a landing page instead of one exact requisition; also noted in the
header. Nothing left to do here.
