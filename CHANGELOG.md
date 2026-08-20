# Changelog

## 0.2.0 — 2026-08-20

Rebuilt from the 2025 sketch into a single runnable package.

- Scrubbed history: removed committed `.env` (two OpenAI keys, both revoked), a 306 MB virtualenv, logs, outputs and caches. `.git` went from 100 MB to under 1 MB.
- Collapsed 22 copy-pasted agent packages into one role registry (`adeptly/roles.py`).
- Router now uses whole-word matching; found in dry-run that `nda` matched inside `agenda`.
- Governance rejects placeholder sections and flags emails/phone numbers, not just missing headings.
- Added the human approval gate (`pending → approved/rejected`, named approver, `--force` requires a note, every decision logged).
- Added an offline dry-run LLM provider so the full loop runs without a key; OpenAI and Anthropic are optional extras.
- Added CLI (`adeptly run|roles|pending|show|approve|reject`).
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
  line and exit 2 instead of a traceback. `--root` / `ADEPTLY_ROOT` added.
- Eval: `--set-baseline` refuses when cases fail; case-count shrinkage counts as regression.
- Version single-sourced from `adeptly/__init__.py`; `VERSION` checked by a test.

## 0.1.0 — 2025-08-15

Initial sketch: SDK contracts, docs, 22 placeholder agents. Did not run.
