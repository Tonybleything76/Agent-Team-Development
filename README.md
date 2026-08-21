# Adeptly Agents

A hierarchical AI consulting team in code: a Router/Supervisor dispatches a task to the right
specialists, a Governance evaluator checks every artifact, and **nothing is released until a named
human approves it**. Built to show how an autonomous agent team stays accountable.

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
                                          adeptly approve --by "<name>"   or   adeptly reject
                                                                     ▼
                                                 out/approved/<run_id>/   |   out/rejected/<run_id>/
```

1. **Router** (`adeptly/router.py`): deterministic keyword rules map a task to an ordered list of
   specialists. Deterministic on purpose — a plan must be explainable and testable. Unmatched tasks
   fall back to the Strategist.
2. **Specialists** (`adeptly/roles.py`): a registry of 22 roles in three tiers — supervisor,
   client-facing, support. Each is a title and a remit; the orchestrator turns that into a system
   prompt. Adding a specialist is one `Role(...)` entry plus a routing rule. Each specialist sees
   the first 600 characters of every predecessor's artifact as context.
3. **Governance** (`adeptly/governance.py`): every artifact must carry Objective, Body, Citations
   (with an https URL inside that section), Risks and Next Steps — plain, markdown or bold
   headings — with no placeholder text (`TBD`, `...`, `-`), nothing shorter than three characters,
   and no email, phone (with separators), SSN-shaped or Luhn-valid card-shaped numbers. Rule-based,
   so it catches shape and obvious leaks, not judgment. Verdict is APPROVE or REVISE and is recorded in the run manifest.
4. **The human gate** (`adeptly/gate.py`): every run lands in `out/pending/`. A run moves to
   `out/approved/` only when someone runs `adeptly approve <run_id> --by "<name>"`. If Governance
   flagged anything — or a specialist errored — approval is refused unless you pass `--force`
   *and* a `--note` saying why, and the manifest records `forced: true` with the flagged roles.
   Rejections require a reason. The decision is written into the
   manifest before the directory moves, so an interrupted decision is never lost, and every
   decision is appended to `logs/runs.jsonl` with who and when. `run_id`s are validated against
   the generated shape; nothing outside `out/` can be addressed.
5. **LLM layer** (`adeptly/llm.py`): `LLM_PROVIDER=dryrun` (default) needs no key and produces
   deterministic output so the whole loop — including the gate — runs in CI. `openai` and
   `anthropic` providers are optional extras.

## Run it

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/Tonybleything76/Agent-Team-Development.git
cd Agent-Team-Development
uv sync                      # creates .venv from the pinned uv.lock
uv run adeptly roles         # the team
uv run adeptly run "Build an AI transformation roadmap and ROI model for a manufacturer"
uv run adeptly pending       # what is waiting for a human
uv run adeptly show <run_id> # read the manifest and every artifact
uv run adeptly approve <run_id> --by "Your Name"
uv run adeptly reject  <run_id> --by "Your Name" --reason "placeholder content"
```

To use a real model: `cp .env.example .env`, set `LLM_PROVIDER` and a key, then
`uv sync --extra openai` (or `--extra anthropic`) and run as above (or pass `--provider`).
The CLI loads `.env` from the current directory (values already in the environment win);
`.env` is git-ignored. Output goes to `./out` and `./logs` — pass `--root <dir>` or set
`ADEPTLY_ROOT` to put them elsewhere. All variables are listed in `.env.example`.

## Test it

```bash
uv run ruff check .          # lint
uv run pytest                # unit tests: router, governance, gate, orchestrator, CLI
uv run python -m evals.run   # scored eval; writes evals/results/latest.json (git-ignored),
                             # fails on regression against the committed evals/results/baseline.json
```

## What this is not

- Not a production deployment. There is no queue, no UI, no auth; the gate is an atomic file move and a log line, on purpose.
- Not connected to tools yet. MCP server wiring from the first sketch was removed because it never worked; re-adding it is the next step once the gate is proven.
- Not a claim about output quality. The dry-run provider exists to prove the control flow, not the content, and the eval is a regression harness over fixed cases — it measures that the rules do what they say, not that routing or governance is good in the wild. The eval's "hard" router cases are there to keep that honest; see `evals/results/latest.json`.
- Not yet exercised against a real model in this repo. The OpenAI and Anthropic providers are unit-tested with fake clients only.

## History

First sketched August 2025 as 22 copy-pasted agent packages on the `mcp-agent` framework; the
code did not run and the repo shipped with a virtualenv and a key. Rebuilt August 2026 as one
package with the gate implemented for real. See `CHANGELOG.md`.

## Layout

```
adeptly/        package: roles, router, governance, llm, orchestrator, gate, storage, cli
tests/          pytest suite
evals/          scored eval cases + runner; results land in evals/results/
docs/           ARCHITECTURE.md — design notes and what is next
```
