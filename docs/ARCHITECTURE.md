# Architecture

## Components

| Component | Module | Responsibility |
|---|---|---|
| Router / Supervisor | `adeptly/router.py` | Task → ordered specialist plan via whole-word keyword rules. Records which rules fired. |
| Role registry | `adeptly/roles.py` | 22 roles in three tiers. Supervisor roles are never dispatched as specialists. |
| Specialist producer | `adeptly/orchestrator.py::produce` | Builds the system/user prompt for a role, calls the LLM, runs Governance. |
| Governance evaluator | `adeptly/governance.py` | Rule-based checks: required sections, no placeholders, ≥1 https citation, no email/phone. |
| Orchestrator | `adeptly/orchestrator.py::run` | Runs the plan sequentially, passes prior output as context, isolates per-specialist failures, writes manifest + log. |
| Human gate | `adeptly/gate.py` | pending → approved/rejected by a named person; refuses approval of governance-flagged or errored runs without `--force` + note; validates `run_id`; records the decision in the manifest before moving. |
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
`error`, logged to `runs.jsonl`, and the run continues. The manifest is written before the first
specialist runs and after every artifact (status `running` until the end), so an interrupted run
is visible in `adeptly pending` and can be rejected. A run with errors can be reviewed and
rejected, or approved with `--force` and a note.

**Manifests are written atomically** (temp file + rename). `pending` surfaces directories with a
missing or corrupt manifest instead of hiding them.

## Data shapes

`manifest.json` (one per run): `run_id, task, provider, plan{roles, matched_rules}, artifacts[{role,
file, review{ok, issues, verdict}, error}], status (running → pending → approved|rejected),
created_at, version, decision{state, by, note, at, forced, flagged_roles}` (decision appears
after approve/reject; `forced` is true when a human overrode governance flags).

`logs/runs.jsonl` events: `run_start, artifact, specialist_error, run_end, approved, rejected`
(decision events carry `by`, `note`, `forced`).

## Accepted limitations (reviewed 2026-08-20)

These were raised in adversarial review and accepted deliberately rather than fixed:

- **The gate records a human decision; it does not authenticate the human.** `--by` is any
  non-empty name. Adding identity/auth would be over-engineering for a single-operator CLI; the
  value is that "who decided, when, why" is a grep-able fact.
- **The eval is a regression harness, not a quality benchmark.** Router and governance are
  rule-based, so fixed cases mostly pass by construction. Eight realistic "hard" router cases are
  included and allowed to fail; their score is reported, not hidden.
- **Context truncation.** Each specialist sees 600 characters of every predecessor's artifact.
- **Concurrency.** Atomic rename is the only primitive; no locking. Two operators deciding the
  same run at once will see one succeed and one get a clear error.
- **`repr(exc)` in manifests.** Provider exceptions are recorded verbatim in runtime output
  (git-ignored); readability beats the theoretical leak.

## Next

1. Tool access via MCP (filesystem, fetch) behind the specialist producer — removed from v0.1 because it never worked; re-add with a test.
2. LLM-backed router behind the same interface, compared against the keyword router using the eval.
3. Governance checks on real model output (tone, accessibility) — currently rule-based only.
