# TODOS

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
