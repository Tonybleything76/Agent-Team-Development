# TODOS

## Phase 4 — the paid proof run

**Status: ready to spend, not yet spent.** Needs a human to decide it is worth the money.

**The task**, rewritten in v0.9.0 so it exercises the roster rather than falling through to the
Strategist:

> Our 2,000-person healthcare operations team has finished the claims copilot pilot and the
> steering committee wants to scale it. Line managers are resisting, nobody has mapped where a
> human stays in the loop, and two workstreams are behind. Legal is asking whether this falls
> under the EU AI Act, and the claims data quality is poor. What do we need to decide before
> go-live?

**Measured on the v0.9.0 router**, `LLM_PROVIDER=dryrun`, run 20260901_144930_dd8b92:

| | Old task | Rewritten task |
|---|---|---|
| Rules fired | none (default) | 6 |
| Roles | 1 (`strategist`) | 6 advisors |
| LLM calls | 3 | 18 |
| `used_default` | true — would now be flagged | false |

Dispatches `value_realization_lead`, `change_management_lead`, `process_excellence_lead`,
`data_readiness_lead`, `program_management_lead`, `governance_advisor`. It reaches adoption,
process and program management, which the plan set as the bar. It does not reach `domain_owner`
or `enterprise_architect` — add "who owns the claims process end to end" and an architecture
question if demonstrating all eight matters more than the extra six calls.

**Before spending:** 18 calls at `LLM_MAX_TOKENS=6000`, inside the 21-call worst case already
measured. The dry run reports `critique: 0 point(s)` because the offline provider's deterministic
output is not parseable as a critique — expected, and the reason the critique loop is only truly
exercised against a live provider.

**Verify first:** `LLM_PROVIDER=dryrun uv run huminloop run "<task above>"`.


## Re-resolve the citation URLs in docs/ROSTER-EVIDENCE.md

**What:** Replace the 47 Vertex AI Search redirect URLs with canonical publisher URLs.

**Why:** That file is the defensibility layer for the 22-role roster — it is what turns "I think
the team looks like this" into a claim that can be cited. Its links are all
`vertexaisearch.cloud.google.com/grounding-api-redirect/...` and may expire. Dead links in a public
repo are worse than no links: they look like sourcing while proving nothing. Flagged by the outside
voice during the 2026-08-26 eng review, and admitted in the file's own header.

**Context:** Mechanical, not research. Every entry names its underlying domain (bcg.com,
mckinsey.com, deloitte.com, accenture.com, ibm.com, kpmg.com, europa.eu), so each redirect can be
resolved once and replaced. Prioritize the three claims worth saying out loud in an interview:

1. BCG's 10-20-70 rule (10% algorithms, 20% technology, 70% people and process) — cites 1, 2, 46.
2. McKinsey's Domain Owner construct, the N-2/N-3 executive who owns end-to-end P&L — cites 3, 4.
3. Deloitte's Trustworthy AI governance framing and its stop/go authority — cites 16, 23, 28.

**Pros:** Makes the evidence file genuinely portfolio-ready and the roster defensible by citation.
**Cons:** An hour of link-chasing that produces no code.

**Depends on / blocked by:** Nothing. Blocks no milestone. Do it before sending the repo to anyone.
