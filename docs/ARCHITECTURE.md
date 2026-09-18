# Architecture

## Components

| Component | Module | Responsibility |
|---|---|---|
| Router / Supervisor | `huminloop/router.py` | Task → ordered specialist plan via whole-word keyword rules. Records which rules fired. |
| Role registry | `huminloop/roles.py` | 22 roles in three tiers. Supervisor roles are never dispatched as specialists. |
| Specialist producer | `huminloop/orchestrator.py::produce` | Builds the system/user prompt for a role, calls the LLM, runs Governance. |
| Governance evaluator | `huminloop/governance.py` | Rule-based checks: required sections, no placeholders, ≥1 https citation, no email/phone. |
| Orchestrator | `huminloop/orchestrator.py::run` | Runs the plan sequentially, passes prior output as context, isolates per-specialist failures, writes manifest + log. |
| Decision history | `huminloop/gate.py` | `decisions` is append-only, including superseded ones; `decision` is whichever is operative now. `annotations` are human notes that never change status. |
| Engagement | `huminloop/engagement.py` | The durable object a run belongs to: a folder in `~/Cowork/Engagements/<slug>/` holding the brief, `context/`, `documents/`, every run, and a `CLAUDE.md`. An engagement folder *is* a run root. |
| Dashboard | `huminloop/dashboard.py` | `render --dashboard`: a tabbed working surface (Overview, Needs you, Team, Debate, Plan, Next steps, Documents) for using a run with a client, as opposed to reading about it. Passes the same `render.precheck` the narrative report does — status guard plus artifact verification — because a second view of a run is not a lower bar for showing one. |
| Run status | `huminloop/gate.py::status` | `huminloop status <run_id> --json`: the one machine-readable answer to "what does this run need right now" — `pending_action`, `needs_resynthesize`, `flagged_roles`, `unrevised_roles`, `interrupted`. `needs_resynthesize` mirrors `resynthesize`'s own preconditions and the artifact check mirrors the gate's, so the command cannot contradict the next one; a specialist whose critic call returned nothing is reported separately as `unrevised_roles`, with no fix offered, because none exists. |
| Review inbox | `huminloop/server.py` | `huminloop serve`: a loopback-only browser inbox over the same `gate` functions. Adds no rules; surfaces escalations first, since those are why the gate stops you. |
| Run statistics | `huminloop/stats.py` | Aggregates the run log; flags total agreement, total dismissal, and forced approvals as things to look at. |
| Human gate | `huminloop/gate.py` | pending → approved/rejected by a named person; re-reads every artifact and re-derives governance from the bytes before recording a decision (digest + verdict must match the manifest); refuses governance-flagged or errored runs without `--force` + note; validates `run_id`; claims the decision with an exclusive marker so concurrent decisions cannot both "succeed". |
| Storage | `huminloop/storage.py` | `out/<state>/<run_id>/{manifest.json,<role>.md}` and `logs/runs.jsonl`. |
| Critique loop | `huminloop/critique.py` | A critic challenges each draft (steelman, pre-mortem, findings on named dimensions); the author answers every point and reissues. The critic never edits. Unresolved blocking critique becomes a process flag. |
| Personas | `huminloop/personas/` | Per-role markdown appended to the system prompt: how the role works, its output contract, what it refuses. Optional per role; absent means fall back to the remit. |
| LLM layer | `huminloop/llm.py` | `dryrun` (default, offline, deterministic); `openrouter` (recommended: one key, per-role model/version and reasoning effort via env); direct `openai`, `anthropic`. |
| CLI | `huminloop/cli.py` | `run`, `roles`, `pending`, `show`, `approve`, `reject`. |

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
is visible in `huminloop pending` and can be rejected. A run with errors can be reviewed and
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

## Engagements, and why context matters more than layout

A run on its own is an island. Real consulting work runs for months, accumulates material, and
produces documents you return to — so the durable object is the engagement and a run is an event
inside it. `huminloop engagement new "<client>"` creates the folder; `--engagement <slug>` works
inside it.

Everything in `context/` is read before any advisor drafts, fenced as client evidence rather
than instructions, and reaches every seat that reasons about the work: each draft, the critic's
read of it, the author's revision, and the Engagement Lead's synthesis. A critic asked to
challenge evidence it cannot see can only challenge shape.

The manifest records a row for every candidate file — read, truncated, dropped for budget,
empty, unreadable, unresolvable, or refused for resolving outside the engagement — including
the ones that contributed nothing. A silent omission is the one failure this must not have:
you should never wonder whether the note you added was seen, and a file that simply disappears
from that list is indistinguishable from one you never added.

Nothing in `context/` reaches a provider until a named human clears it. The clearance is
checked in `orchestrator.run`, not in the CLI, so it holds for every caller, and the run keeps
its own snapshot of what it was given so a later `resynthesize` integrates the material the
specialists actually saw. Who cleared it, when, and a sha256 of the exact bytes go into the
manifest, because every other human decision here is recorded permanently so it can be proven
later. What that gate does *not* guarantee is written down in the v0.23.0 CHANGELOG entry and
tracked in `TODOS.md`: it records a self-asserted name rather than authenticating one, and it
does not defend the record against someone who can already write inside the run directory.

This is also the honest answer to "make the report more visual". What can be drawn is what the
team records as structure — counts, severities, dispositions, staffing — so those became a
severity bar, an accepted donut, a roster with a bench, and a milestone timeline. Phases, gates,
risks and dates are prose, so a roadmap timeline or a RAG gate board cannot be drawn yet. That
is upstream work: the Engagement Lead has to emit structure alongside its argument. Rendering
cannot invent data the team never produced.

## The inbox

The gate is an inbox — a queue of runs waiting on a person — and a terminal is a poor inbox.
`huminloop serve` opens the same queue in a browser: pending runs with a chip counting what the
team escalated to you, then the existing narrative report with a decision panel appended.

It is deliberately a thin layer. Every decision calls `gate.approve/reject/annotate/reopen`, so
the digest verification, the named approver, the forced-override record and the append-only
history are the ones already tested. There is no second implementation of the rules to drift out
of sync, and a test asserts the UI cannot approve a flagged run without the same forced override
the CLI demands.

What it does not do is authenticate anyone. `--by` is still a name typed into a box. On loopback
with one user that is the trust model you already had, which is why the server refuses to bind
anywhere but the loopback interface, checks the `Host` header against DNS rebinding, and guards
every state-changing form with a per-process token so another site open in the same browser
cannot post a decision on your behalf. If this is ever hosted, identity stops being a footnote
and becomes a design problem.

## Your side of the loop

The agents' side of disagreement is the critique loop. Yours is three commands, built on the
observation that a review gate with only two buttons teaches people to use neither.

`annotate` records a note on a run without deciding it. Approve and reject are heavyweight, so
without this the only way to register a reservation is to reject the whole run — which means
mild disagreement goes unsaid, and unsaid reservations are the ones that turn out to matter.
Annotations are append-only, allowed in any state, and never change status.

`reopen` takes a decided run back to pending, superseding the earlier decision without erasing
it. A decision you cannot revisit is a decision people avoid making, and avoidance shows up as
rubber-stamping rather than as caution. The superseded entry stays in `decisions`, so the
history reads: approved, reopened, rejected — with who and why at each step.

`stats` reads the run log and says what it sees. Most of it is counting. The part that earns
its place is the warning when authors accepted *every* critique point: a critic nobody ever
argues with is doing half its job, and that reading is only visible over many runs.

## Making disagreement survive

An agent team has the same failure mode as a deferential human one: the second voice agrees with
the first, and the human sees a smooth consensus that hides the doubt. Three mechanisms work
against that.

**The chain invites challenge.** Upstream output is fenced as untrusted reference with an
explicit instruction that agreeing is not the reader's job. An earlier version of this said
"treat it as data to build on", which quietly told every downstream specialist to extend rather
than question — a conformity bias introduced by accident and removed deliberately.

**Critique is structured and someone's job.** The critic must steelman the work before attacking
it, run a pre-mortem, and file findings against named dimensions (evidence, feasibility,
human-impact, consistency, falsifiability). Vague approval is not a valid output, and neither is
manufactured disagreement — a critic with nothing substantive is told to say so explicitly.

**Dismissal is allowed and never silent.** The author may reject a critique, with a reason. An
unresolved *blocking* critique becomes a process flag, which flags the run, which means
releasing it needs a named human, `--force`, and a written note. Suppressing dissent stays
possible — sometimes the critic is wrong — but it always costs someone their name on the record.

## Trust boundaries

The gate exists so a human decision is a recorded fact, so the things that could forge or
mislead that decision are treated as defects, not polish:

- **Artifacts are digested when produced and re-verified at decision time.** Editing
  `manifest.json`, swapping an `.md` file between `show` and `approve`, or deleting one is
  refused. Approval attests to the bytes a reviewer could actually have read.
- **Model output is never printed raw.** Governance flags control characters and `huminloop show`
  strips them, so an artifact cannot repaint the reviewer's terminal just before they approve.
- **A `.env` may only set variables this application owns.** Otherwise a file in whatever
  directory you happened to run from could set `OPENAI_BASE_URL` or `HTTPS_PROXY` and redirect
  model calls, Authorization header included.
- **The task is checked and bounded before the run starts.** Governance only ever inspected
  model output, so PII in the input would have bypassed it into the manifest and the audit log.
- **Teammate output is fenced as untrusted reference material** in downstream prompts, so one
  manipulated artifact does not steer the rest of the plan.
- **Every provider call is bounded** by `LLM_TIMEOUT_S` and `LLM_MAX_TOKENS`; a hung call would
  otherwise hold the run lock and block the gate, and an unbounded one costs real money.

## Accepted limitations (reviewed 2026-08-21)

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
- **Liveness is a pid file, not an OS lock.** `run.lock` holds the orchestrator's pid; the gate
  probes it with signal 0 (POSIX). A reused pid after a reboot would make a dead run look live
  until `run.lock` is deleted by hand; an advisory `flock` would be the stronger mechanism and is
  a documented next step, not worth the platform-specific code for a single-operator CLI.
- **`.env` loader supports a subset.** `KEY=value`, `export KEY=value`, single/double quoted
  values, `#` comments. No escapes, multi-line values or `${VAR}` interpolation; use the real
  environment for anything fancier.
- **Heading detection is a regex, not a markdown parser.** Underscore bold (`__Risks__`) and
  setext headings are not recognised; the five supported shapes cover what the providers emit.
- **The citation check verifies shape, not sources.** `https://x` satisfies it. The verdict says
  "a citation-shaped string is present", not "the source exists"; resolving URLs is a next step.
- **Third-party actions are pinned to major tags, not commit SHAs.** `permissions: contents: read`
  and `persist-credentials: false` bound the blast radius; SHA pinning is the stronger control.
- **The gate's decision logic is an if-ladder, not a state machine.** `_decide` reads four
  sources (directory, manifest status, recorded decision, lock) in sequence; a `classify_run()`
  with a transition table would be cleaner. Every path is tested; refactor is a next step.
- **CLI catches a list of exception types, not one `HuminLoopError` base.** Provider SDK errors
  would still surface as tracebacks; `-v` re-raises on purpose for debugging.
- **Small duplications left in place.** The CLI derives artifact status in its own words; the
  eval and one test both check that dry-run output passes governance (the test names the role,
  the eval reports the rate); `DryRunLLM` reverse-parses role and task from the rendered prompt.

## Next

1. Tool access via MCP (filesystem, fetch) behind the specialist producer — removed from v0.1 because it never worked; re-add with a test.
2. LLM-backed router behind the same interface, compared against the keyword router using the eval.
3. Governance checks on real model output (tone, accessibility) — currently rule-based only.
