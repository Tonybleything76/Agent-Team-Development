# Architecture

## Components

| Component | Module | Responsibility |
|---|---|---|
| Router / Supervisor | `adeptly/router.py` | Task → ordered specialist plan via whole-word keyword rules. Records which rules fired. |
| Role registry | `adeptly/roles.py` | 22 roles in three tiers. Supervisor roles are never dispatched as specialists. |
| Specialist producer | `adeptly/orchestrator.py::produce` | Builds the system/user prompt for a role, calls the LLM, runs Governance. |
| Governance evaluator | `adeptly/governance.py` | Rule-based checks: required sections, no placeholders, ≥1 https citation, no email/phone. |
| Orchestrator | `adeptly/orchestrator.py::run` | Runs the plan sequentially, passes prior output as context, isolates per-specialist failures, writes manifest + log. |
| Human gate | `adeptly/gate.py` | pending → approved/rejected by a named person; refuses approval of governance-flagged runs without `--force` + note. |
| Storage | `adeptly/storage.py` | `out/<state>/<run_id>/{manifest.json,<role>.md}` and `logs/runs.jsonl`. |
| LLM layer | `adeptly/llm.py` | `dryrun` (default, offline, deterministic), `openai`, `anthropic`. |
| CLI | `adeptly/cli.py` | `run`, `roles`, `pending`, `show`, `approve`, `reject`. |

## Design decisions

**Deterministic routing.** An LLM could classify tasks better, but a keyword router is
explainable, testable, and costs nothing. The plan is recorded with the rules that fired so a
reviewer can see why a specialist was involved. Swap in an LLM router later behind the same
`Router.route(task) -> Plan` interface.

**Governance is separate from production.** The evaluator never edits text; it only returns a
verdict and issues. That keeps the check cheap, repeatable and the same for every role.

**The gate is dumb on purpose.** Approval is a directory move plus an append-only log line. No
database, no service. That is enough to make "who released this, when, and why" a fact you can
grep, and easy to replace with a real queue later.

**Dry-run by default.** The control flow — routing, context passing, governance, gate — is what
this repo proves. Everything runs in CI without a key. Real providers are opt-in extras.

**Failures are isolated and logged.** A specialist that raises is recorded in the manifest with
`error`, logged to `runs.jsonl`, and the run continues. A run with errors can still be reviewed
and rejected by a human.

## Data shapes

`manifest.json` (one per run): `run_id, task, provider, plan{roles, matched_rules}, artifacts[{role,
file, review{ok, issues, verdict}, error}], status, created_at, version, decision{state, by,
note, at}` (decision appears after approve/reject).

`logs/runs.jsonl` events: `run_start, artifact, specialist_error, run_end, approved, rejected`.

## Next

1. Tool access via MCP (filesystem, fetch) behind the specialist producer — removed from v0.1 because it never worked; re-add with a test.
2. LLM-backed router behind the same interface, compared against the keyword router using the eval.
3. Governance checks on real model output (tone, accessibility) — currently rule-based only.
