# Changelog

## 0.7.0 — 2026-09-01

The roster is an AI transformation engagement team, not a small agency.

The repo argued that transformation fails for human-system reasons, then staffed twenty
specialists with no change-management, adoption, readiness or workforce advisor anywhere in them.
Five of the nine advisory domains the team claims to cover had no dispatchable role at all. That
gap — not missing tooling — is why the team could not be trusted on real work.

- **Deleted six agency roles**: `social_manager`, `oem_partner`, `ea`, `it`, `marketing`,
  `content_creator`. They ran a business rather than delivering an engagement. Five routing rules
  died with them (campaign, social, it, partner, admin); the router goes from 18 rules to 13.
- **Added eight transformation advisors**: `domain_owner`, `value_realization_lead`,
  `change_management_lead`, `process_excellence_lead`, `data_readiness_lead`,
  `enterprise_architect`, `program_management_lead`, `governance_advisor`. Each carries the
  decision it owns, not just a topic.
- **Rewrote `product_manager`** as the AI Product Manager rather than adding a second, near-identical
  PM seat. The research names this one of the three chronically understaffed engagement roles.
- `len(SPECIALISTS)` 20 → 22. `dryrun_specialists` and `specialists_receiving_house_brief` read 22;
  `persona_coverage` is now 5/22 = 0.227, down from 0.250 — the denominator grew, the numerator
  did not. Personas for the new advisors are the next piece of work.
- Roster is evidence-backed: `docs/ROSTER-EVIDENCE.md`, 47 cited sources across Deloitte, PwC, EY,
  KPMG, McKinsey, BCG, Accenture and IBM. Every added seat traces to a role those firms actually
  staff, with the decision it owns.

**`router_hard_exact_rate` went 0.875 → 1.000 and this is not an improvement.** The only failing
hard case was `h05`, which tested a genuine ambiguity between an EA meeting summary and
cybersecurity. Deleting `ea` voided the ambiguity, so the case now passes mechanically. It is
retargeted with a note saying exactly this. A real ambiguity should replace it when the
transformation routing vocabulary is written. Treat the 1.000 as an artifact of the roster change.

**Nine router eval cases were retargeted, never removed.** `evals/run.py` treats a shrinking
`router_cases` or `router_easy_cases` as a regression, deliberately, so deleting the orphaned cases
would have failed CI and the fix would have been to disarm the guard. `r04`, `r05`, `r16`, `r17`,
`r18`, `r21`, `r23` and `h07` describe agency work with no seat on the new roster; each now records
the honest outcome — a fallback to the Strategist — with a note. Counts hold at 32 and 24.

**Interim state, stated plainly:** the eight new advisors have one-line remits and no routing rules
yet. Nothing dispatches to them, and without personas they will produce generic output — the same
failure this change exists to fix. This release makes the roster right; it does not yet make the
team good. Routing vocabulary and personas follow.

## 0.6.0 — 2026-08-22

Critique loop, so disagreement changes the deliverable instead of decorating it.

- A critic challenges every draft: steelman first, then a pre-mortem, then findings against named
  dimensions (evidence, feasibility, human-impact, consistency, falsifiability). The critic never
  edits; the author answers each point and reissues, so authorship and accountability stay together.
- Dismissal is allowed and never silent: an unresolved blocking critique flags the run, so
  releasing it needs a named human, --force and a written note.
- Removed a conformity bias introduced in 0.4.0: the chain told downstream specialists to treat
  teammate output as "data to build on". It now says agreeing is not their job.
- Split byte-derived `review` from `process_flags`. The gate re-derives the review from the
  artifact bytes; findings the bytes cannot show (truncation, dismissed critique) travel
  separately. This also fixed a latent bug where a truncated-but-complete artifact would have
  made the gate refuse to decide.
- House brief gained a "disagree well" standard.

## 0.5.0 — 2026-08-22

- Shared house brief (`huminloop/personas/_house.md`) sent to every specialist, personified or
  not: pair technical rigour with the human impact of the change. Name who works differently and
  what they lose, respect the expertise being automated, specify the human checkpoint where a
  system gains authority over safety, money or someone's job, and say "headcount reduction" in
  those words rather than laundering it into "productivity". Gated in the eval as
  `specialists_receiving_house_brief` (20/20).
- Pre-Sales and Finance personas, completing the `proposal` route (pre_sales, legal, finance) as
  a second fully persona-driven workflow. Coverage 5/20, reported not hidden.
- Default token budget 4000 → 6000: the third specialist in a three-role chain carries the most
  upstream context and was still being truncated. The truncation flag caught it, which is what
  it is for.
- Second committed example run at `docs/example-run/proposal/`.

## 0.4.0 — 2026-08-21

- Persona layer: per-role markdown in `huminloop/personas/`, appended to the house contract and
  editable without touching Python. Written: strategist, data_scientist (the `strategy` route is
  now fully persona-driven) and legal (support tier, defined by what it refuses).
- Eval gates `personas_written` and `personas_well_formed`, and reports `persona_coverage`
  (3/20) rather than implying the roster is finished.
- `docs/example-run/` carries real provider output, so the system can be judged without a key.

## 0.3.1 — 2026-08-21

First run against a real provider (OpenRouter, anthropic/claude-sonnet-5), which found a defect
no dry run could: both specialists hit the 2000-token cost cap mid-sentence, so Citations, Risks
and Next Steps were never written and governance reported them as "Missing section" — an
operational failure wearing a content failure's clothes.

- Providers now return a `Completion` carrying whether the model stopped on the token budget,
  and a truncated artifact is reported as "Output truncated at the token budget", listed first.
- Default `LLM_MAX_TOKENS` raised 2000 → 4000, and the system prompt now tells the model to
  budget its length so every section fits.
- Renamed the package and CLI from `adeptly` to `huminloop`.

## 0.3.0 — 2026-08-21

Security and integrity pass on the gate itself, driven by adversarial review. See the 0.2.0
entry for the rebuild; this release is what pre-merge review found in it.

## 0.2.0 — 2026-08-20

Rebuilt from the 2025 sketch into a single runnable package.

- Scrubbed history: removed committed `.env` (two OpenAI keys, both revoked), a committed virtualenv (14,526 files), logs, outputs and caches. `.git` went from 100 MB to 168 KB (measured with `du -sh .git` before and after `git filter-repo`, 2026-08-20; the pre-scrub objects are gone from this repo, so the figure is not re-derivable here).
- Collapsed 22 copy-pasted agent packages into one role registry (`huminloop/roles.py`).
- Router now uses whole-word matching; found in dry-run that `nda` matched inside `agenda`.
- Governance rejects placeholder sections and flags emails/phone numbers, not just missing headings.
- Added the human approval gate (`pending → approved/rejected`, named approver, `--force` requires a note, every decision logged).
- Added an offline dry-run LLM provider so the full loop runs without a key; OpenAI and Anthropic are optional extras.
- Added CLI (`huminloop run|roles|pending|show|approve|reject`).
- Pinned dependencies with `uv.lock`; Python 3.11+.
- Removed the unpinned `mcp-agent @ git+main` dependency and the MCP wiring that never worked.

Found in review and fixed before release:

- Gate: `run_id` was joined onto a path unvalidated; `approve ../approved/<id>` could flip a
  decided run. Now validated against the generated shape.
- Gate: approving a run with an errored specialist crashed; errored artifacts now count as
  flagged (need `--force` + note).
- Gate: decision was move-then-write; now the manifest records the decision first, then moves,
  and refuses to merge into an existing destination.
- Orchestrator: manifest is written from the start and after every artifact, so Ctrl-C leaves a
  visible `running` run instead of an orphan directory.
- Governance: accepted markdown/bold headings; required `Body`; URL must be in Citations and be
  https; flagged decorated placeholders (`TBD.`), one-char sections, more phone formats, SSN and
  card shapes; a URL on the line after `Citations:` no longer reads as an empty section.
- Governance: section regex swallowed the newline after a bare `Risks:` heading (found by eval).
- Router: `nda` matched inside `agenda` (found in dry-run); common single words (`lead`,
  `script`, `thread`, `summary`, `meeting`, `retention`, `sequence`, `partner`) tightened to
  phrases. Eight realistic ambiguous cases added to the eval and allowed to fail.
- CLI: `.env` was documented but never loaded; now loaded (environment wins). Errors print one
  line and exit 2 instead of a traceback. `--root` / `HUMINLOOP_ROOT` added.
- Eval: `--set-baseline` refuses when cases fail; case-count shrinkage counts as regression.
- Version single-sourced from `huminloop/__init__.py`; `VERSION` checked by a test.
- OpenRouter provider (`LLM_PROVIDER=openrouter`): one key, any vendor's models; model/version
  and reasoning effort resolved per specialist role from env (`OPENROUTER_MODEL_<ROLE>`,
  `OPENROUTER_EFFORT_<ROLE>`), with global fallbacks. `generate()` now receives the role key.
- Second review pass: `--force` was briefly persisted into the manifest and could leak into a
  later plain approve — replaced with a parameter and a recorded `decision.forced`; interrupted
  (`running`) runs can be rejected but not approved; numbered markdown headings recognised;
  body bullets starting with a section word no longer read as headings; phone needs separators
  and card shapes need a Luhn pass (no false PII on figures/years); inline `#` comments in
  `.env` stripped; `OSError` handled as a one-line CLI error; tests hermetic (`HUMINLOOP_ENV_FILE`,
  `HUMINLOOP_ROOT`); eval gates only regression-guard metrics so honest hard-case failures are
  never "regressions"; `latest.json` git-ignored, `baseline.json` is the committed record.
- Pre-merge adversarial review (Codex plus a fresh-context subagent) found three defects that
  defeated the gate itself, all fixed with tests: artifact bytes were never verified, so editing
  one field in `manifest.json` turned a flagged run into a clean approval; `huminloop show` printed
  model output raw, so ANSI escapes could repaint the reviewer's terminal just before approval;
  and `.env` could set any variable, including `OPENAI_BASE_URL`, redirecting model calls with
  the key attached.
- Also fixed: provider calls are bounded by timeout and max-tokens; a provider error or empty
  completion raises instead of writing an empty artifact; blank env vars fall back to defaults;
  invalid pids in `run.lock` no longer report a dead run as live; a manifest whose `run_id`
  disagrees with its directory is surfaced as corrupt; concurrent decisions are serialised by an
  exclusive claim; the task is length-bounded and PII-checked before the run starts; teammate
  output is fenced as untrusted in downstream prompts; CI runs once per PR with
  `persist-credentials: false`, a job timeout and provider extras installed.
- Third and fourth passes: a `run.lock` (pid) marks a live orchestrator so a run cannot be
  decided out from under it; a decision recorded in the manifest but not yet moved can only be
  completed (same decision) — never overwritten — and the log names the original decider; the
  rename is atomic and never merges directories; orphan pending directories (crash before the
  first manifest write) can be rejected; pluralised labels ("Objectives:", "Next Step:") and
  numbered markdown headings accepted while bold words in prose are not headings; `.env`
  `export` prefix and quoted-values-with-comments parsed; `--root` overrides `ARTIFACT_DIR`/
  `LOG_DIR`; `-v` re-raises for a traceback; eval regression is now judged per case id against
  the baseline (a case that passed and now fails), plus non-shrinking case counts.

## 0.1.0 — 2025-08-15

Initial sketch: SDK contracts, docs, 22 placeholder agents. Did not run.
