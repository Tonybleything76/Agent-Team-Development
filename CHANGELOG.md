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

## 0.1.0 — 2025-08-15

Initial sketch: SDK contracts, docs, 22 placeholder agents. Did not run.
