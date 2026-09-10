# Example run (real provider)

Committed output from an actual run so the system can be judged without a key or a spend.

- Task: `Build an AI transformation roadmap and ROI model for a mid-size manufacturer`
- Provider: OpenRouter, `anthropic/claude-sonnet-5`, 2026-08-21
- Plan: `['strategist', 'data_scientist']`, matched by the `strategy` rule
- Governance: APPROVE on both artifacts
- Reproduce: `LLM_PROVIDER=openrouter huminloop run "<task>" --provider openrouter`

`manifest.json` is the record the gate reads: per-artifact governance verdict and a SHA-256 of
the bytes. Editing an artifact after the fact makes the digest disagree and the gate refuses to
record a decision.

## What the persona changed

The Strategist persona (`huminloop/personas/strategist.md`) requires every figure to carry a
source or an explicit `[ASSUMPTION: ...]` label. The same task run before the persona existed
produced confident benchmark numbers with no labels; with the persona it produces, for example:

> [ASSUMPTION: 500 unplanned downtime hrs/yr × $8,000/hr avg cost × 25% reduction = $1.0M gross
> benefit — every input must be replaced with client CMMS/finance data before this number is
> cited to the CFO]

That is the difference between a deliverable that reads well and one you could defend in front
of a CFO. It is also the clearest argument for personas over prompt-tuning: the rule lives in a
file a human owns, not in the model's discretion.

## Other runs in this directory

- `critique/` — the same roadmap task after the critique loop was added (2026-08-22)
- `proposal/` — the fully persona-driven proposal route (2026-08-22)
- `synthesis/` — the Engagement Lead synthesising a multi-specialist run
- `enablement/` — an AI enablement programme where a critic caught a citation that did not
  support its claim (2026-09-09)

