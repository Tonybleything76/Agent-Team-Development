# HuminLoop Agents

A hierarchical AI consulting team in code: a Router/Supervisor dispatches a task to the right
specialists, a Governance evaluator checks every artifact, and **a named human must approve every
run before it leaves `pending/`**. Built to show how an autonomous agent team stays accountable.

> Status: working prototype, v0.2.0. Runs fully offline by default. See "What this is not" below.

## Why it exists

The Big Four sell AI transformation with large, layered teams: client-facing strategists and
pre-sales alongside legal, privacy, finance, HR, IT and QA in support. This repo models that team
as 20 specialist agents plus two supervisor roles, and puts the part that matters most — who
decides what goes out the door — in a place you can read, test and audit.

The design principle is the one I use in consulting: humans own judgment and release; agents
execute analysis and drafting at speed. The code enforces a recorded human decision before
anything leaves `pending/`; it does not authenticate who that human is (it is a single-operator
CLI), and it says so.

## How it works

```
task ──▶ Router ──▶ [specialist 1] ─▶ [specialist 2] ─▶ … ──▶ Governance check (each artifact)
                          │                                          │
                          └── prior output is passed as context ─────┘
                                                                     ▼
                                                        out/pending/<run_id>/  ◀── waits here
                                                                     │
                                          huminloop approve --by "<name>"   or   huminloop reject
                                                                     ▼
                                                 out/approved/<run_id>/   |   out/rejected/<run_id>/
```

1. **Router** (`huminloop/router.py`): deterministic keyword rules map a task to an ordered list of
   specialists. Deterministic on purpose — a plan must be explainable and testable. Unmatched tasks
   fall back to the Strategist.
2. **Specialists** (`huminloop/roles.py`): a registry of 22 roles in three tiers — supervisor,
   client-facing, support. Each is a title and a remit; the orchestrator turns that into a system
   prompt. Adding a specialist is one `Role(...)` entry plus a routing rule. Each specialist sees
   the first 600 characters of every predecessor's artifact as context.
3. **Governance** (`huminloop/governance.py`): every artifact must carry Objective, Body, Citations
   (with an https URL inside that section), Risks and Next Steps — plain, markdown or bold
   headings — with no placeholder text (`TBD`, `...`, `-`), nothing shorter than three characters,
   and no email, phone (with separators), SSN-shaped or Luhn-valid card-shaped numbers. Rule-based,
   so it catches shape and obvious leaks, not judgment. Verdict is APPROVE or REVISE and is recorded in the run manifest.
4. **The human gate** (`huminloop/gate.py`): every run lands in `out/pending/`. A run moves to
   `out/approved/` only when someone runs `huminloop approve <run_id> --by "<name>"`. If Governance
   flagged anything — or a specialist errored — approval is refused unless you pass `--force`
   *and* a `--note` saying why, and the manifest records `forced: true` with the flagged roles.
   Rejections require a reason. The decision is written into the
   manifest before the directory moves, so an interrupted decision is never lost, and every
   decision is appended to `logs/runs.jsonl` with who and when. `run_id`s are validated against
   the generated shape; nothing outside `out/` can be addressed.
5. **LLM layer** (`huminloop/llm.py`): `LLM_PROVIDER=dryrun` (default) needs no key and produces
   deterministic output so the whole loop — including the gate — runs in CI. `openrouter` is
   the recommended real provider: one key, any vendor's models, and the model is resolved per
   specialist role (`OPENROUTER_MODEL_<ROLE>` beats `OPENROUTER_MODEL` beats the package
   default) and so is reasoning effort (`OPENROUTER_EFFORT_<ROLE>` / `OPENROUTER_EFFORT`,
   low|medium|high), so each task runs on the right model, version and effort. Direct `openai`
   and `anthropic` providers remain as optional extras.

## Run it

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/Tonybleything76/Agent-Team-Development.git
cd Agent-Team-Development
uv sync                      # creates .venv from the pinned uv.lock
uv run huminloop roles         # the team
uv run huminloop run "Build an AI transformation roadmap and ROI model for a manufacturer"
uv run huminloop pending       # what is waiting for a human
uv run huminloop show <run_id> # read the manifest and every artifact
uv run huminloop approve <run_id> --by "Your Name"
uv run huminloop reject  <run_id> --by "Your Name" --reason "placeholder content"
```

To use a real model: `cp .env.example .env`, set `LLM_PROVIDER=openrouter` and
`OPENROUTER_API_KEY`, then `uv sync --extra openai` (OpenRouter speaks the OpenAI
protocol, so it uses the same extra; direct `openai`/`anthropic` work the same way)
and run as above (or pass `--provider`).
The CLI loads `.env` from the current directory (values already in the environment win);
`.env` is git-ignored (`--env-file <path>` to use another). Output goes to `./out` and `./logs`
— set `HUMINLOOP_ROOT` or pass `--root <dir>` *before* the subcommand (`huminloop --root /tmp/x run
"…"`) to put them elsewhere. `huminloop pending --state approved|rejected` lists decided runs.
All variables are listed in `.env.example`.

## See it work without a key

`docs/example-run/` holds real output from an actual OpenRouter run — both artifacts, plus the
`manifest.json` the gate reads, including the per-artifact SHA-256. Nothing there is a mock.

The same task run before the Strategist persona existed produced confident benchmark figures
with no sourcing. With the persona it produces labelled assumptions:

```
[ASSUMPTION: 500 unplanned downtime hrs/yr x $8,000/hr avg cost x 25% reduction = $1.0M gross
benefit - every input must be replaced with client CMMS/finance data before this number is
cited to the CFO]
```

That rule lives in `huminloop/personas/strategist.md`, a file a human edits, not in a prompt
buried in code.

## Personas

A role's one-line remit is enough to route and to test. It is not enough to produce work worth
reviewing. A persona adds how the specialist works, what its output must carry, and what it
must refuse — as markdown in `huminloop/personas/<role>.md`, appended to the contract every
specialist owes regardless of role. Roles without a persona fall back to their remit, so the
layer is additive.

Three are written: `strategist` and `data_scientist` (which together cover the whole `strategy`
route, so that workflow is fully persona-driven), and `legal` as a support-tier example whose
defining feature is the boundary it refuses to cross — it never opines on the law and routes
anything needing counsel to a human. The eval gates that personas stay well-formed and reach
the prompt; it does not grade the writing.

## Test it

CI (`.github/workflows/ci.yml`) runs exactly these on every push and pull request; the eval step
fails the build on any case that passed at baseline and fails now.

```bash
uv run ruff check .          # lint
uv run pytest                # unit tests: router, governance, gate, orchestrator, CLI
uv run python -m evals.run   # scored eval; writes evals/results/latest.json (git-ignored),
                             # fails on regression against the committed evals/results/baseline.json
```

## What this is not

- Not a production deployment. There is no queue, no UI, no auth; the gate is an atomic file move and a log line, on purpose.
- Not connected to tools yet. MCP server wiring from the first sketch was removed because it never worked; re-adding it is the next step once the gate is proven.
- Not a claim about output quality. The dry-run provider exists to prove the control flow, not the content, and the eval is a regression harness over fixed cases — it measures that the rules do what they say, not that routing or governance is good in the wild. The eval's "hard" router cases are there to keep that honest; see the committed `evals/results/baseline.json` (and `latest.json` after you run the eval).
- Only 3 of 20 specialists have a persona. The rest fall back to a one-line remit and will produce generic output; that is visible in `persona_coverage` rather than hidden.
- The unit tests exercise the providers with fake clients. Real-provider behaviour is evidenced by the committed example run, not by the test suite.

## History

First sketched August 2025 as 22 copy-pasted agent packages on the `mcp-agent` framework; the
code did not run and the repo shipped with a virtualenv and a key. Rebuilt August 2026 as one
package with the gate implemented for real. See `CHANGELOG.md`.

## Layout

```
huminloop/        package: roles, router, governance, llm, orchestrator, gate, storage, cli
tests/          pytest suite
evals/          scored eval cases + runner; results land in evals/results/
docs/           ARCHITECTURE.md — design notes and what is next
```
