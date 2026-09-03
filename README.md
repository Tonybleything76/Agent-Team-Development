# HuminLoop Agents

A hierarchical AI consulting team in code: a Router/Supervisor dispatches a task to the right
specialists, a critic challenges every draft before it moves on, a Governance evaluator checks
every artifact, and **a named human must approve every run before it leaves `pending/`**. Built
to show how an autonomous agent team stays accountable.

> Status: working prototype, v0.9.0. Runs fully offline by default. See "What this is not" below.

## Why it exists

The Big Four staff an AI transformation engagement with a layered team: a domain owner who decides
which processes get redesigned, a change and adoption lead who owns organizational readiness, a
value realization lead who decides whether a pilot earned the right to scale, plus data, architecture,
programme and governance seats around them. This repo models that team as 22 specialist agents and
two supervisors, and puts the part that matters most — who decides what goes out the door — in a
place you can read, test and audit.

The roster is not invented. `docs/ROSTER-EVIDENCE.md` traces every seat, and the decision it owns,
to published material across Deloitte, PwC, EY, KPMG, McKinsey, BCG, Accenture and IBM.

The design principle is the one I use in consulting: humans own judgment and release; agents
execute analysis and drafting at speed. The code enforces a recorded human decision before
anything leaves `pending/`; it does not authenticate who that human is (it is a single-operator
CLI), and it says so.

## How it works

```
task ──▶ Router ──▶ [specialist 1] ─▶ [specialist 2] ─▶ … ──▶ Governance check (each artifact)
                          │                                          │
                          │  each draft: a critic challenges it,     │
                          │  the author answers every point          │
                          │  and reissues                            │
                          │                                          │
                          └── prior output passed on as ─────────────┘
                              untrusted reference
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
2. **Specialists** (`huminloop/roles.py`): a registry of 24 roles in three tiers — supervisor,
   client-facing, support. Each is a title and a remit; the orchestrator turns that into a system
   prompt. Adding a specialist is one `Role(...)` entry plus a routing rule. Each specialist sees
   the first 600 characters of every predecessor's artifact, fenced as untrusted reference material
   with an explicit instruction that agreeing is not their job.
3. **Critique loop** (`huminloop/critique.py`): before an artifact is finalised, a critic (QA/QC)
   must steelman it, run a pre-mortem, and file findings against named dimensions — evidence,
   feasibility, human-impact, consistency, falsifiability — each with a severity. The critic never
   edits. The author answers every point, accepts or rejects each with a reason, and reissues, so
   authorship and accountability stay together. An unresolved *blocking* critique flags the run,
   which means releasing it needs a named human, `--force` and a written note. Dismissal is
   allowed; silent dismissal is not.
4. **Governance** (`huminloop/governance.py`): every artifact must carry Objective, Body, Citations
   (with an https URL inside that section), Risks and Next Steps — plain, markdown or bold
   headings — with no placeholder text (`TBD`, `...`, `-`), nothing shorter than three characters,
   and no email, phone (with separators), SSN-shaped or Luhn-valid card-shaped numbers. Rule-based,
   so it catches shape and obvious leaks, not judgment. Verdict is APPROVE or REVISE and is recorded
   in the run manifest. Byte-derived `review` is kept separate from `process_flags` — findings the
   bytes cannot show, like truncation or a dismissed critique — so the gate can re-derive one from
   the artifact and still see the other.
5. **The human gate** (`huminloop/gate.py`): every run lands in `out/pending/`. A run moves to
   `out/approved/` only when someone runs `huminloop approve <run_id> --by "<name>"`. If Governance
   flagged anything — or a critique went unresolved, or a specialist errored — approval is refused
   unless you pass `--force` *and* a `--note` saying why, and the manifest records `forced: true`
   with the flagged roles. Rejections require a reason. The decision is written into the manifest
   before the directory moves, so an interrupted decision is never lost, and every decision is
   appended to `logs/runs.jsonl` with who and when. `run_id`s are validated against the generated
   shape; nothing outside `out/` can be addressed.
6. **LLM layer** (`huminloop/llm.py`): `LLM_PROVIDER=dryrun` (default) needs no key and produces
   deterministic output so the whole loop — including the gate — runs in CI. `openrouter` is
   the recommended real provider: one key, any vendor's models, and the model is resolved per
   specialist role (`OPENROUTER_MODEL_<ROLE>` beats `OPENROUTER_MODEL` beats the package
   default) and so is reasoning effort (`OPENROUTER_EFFORT_<ROLE>` / `OPENROUTER_EFFORT`,
   low|medium|high), so each task runs on the right model, version and effort. Direct `openai`
   and `anthropic` providers remain as optional extras.

## Making disagreement survive

An agent team has the same failure mode as a deferential human one: the second voice agrees with
the first, and the human sees a smooth consensus that hides the doubt. An earlier version of the
chain told downstream specialists to treat teammate output as "data to build on", which quietly
instructed every one of them to extend rather than question. That was a conformity bias introduced
by accident in 0.4.0 and removed deliberately in 0.6.0.

What replaced it: upstream work arrives fenced as untrusted reference, challenge is a named role's
actual job rather than an optional courtesy, and dismissing a critique is permitted but always
costs someone their name on the record. `docs/example-run/critique/` shows a real run of it,
including the caveat that in that run the authors accepted all nine findings — which may mean the
critiques were good, or may be the same agreeableness the loop exists to fight, pointed the other
way.

## Personas

A role's one-line remit is enough to route and to test. It is not enough to produce work worth
reviewing. A persona adds how the specialist works, what its output must carry, and what it
must refuse — as markdown in `huminloop/personas/<role>.md`, appended to the contract every
specialist owes regardless of role. Roles without a persona fall back to their remit, so the
layer is additive.

Every specialist, personified or not, receives the shared house brief
(`huminloop/personas/_house.md`): pair technical rigour with the human impact of the change, name
who works differently and what they lose, respect the expertise being automated, specify the human
checkpoint where a system gains authority over safety, money or someone's job, and say "headcount
reduction" in those words rather than laundering it into "productivity". The eval gates that all
22 specialists receive it.

All 22 specialists have a persona. Each carries a `## Where I stop and ask` section, gated by
the eval: the Value Realization Lead will not call a pilot successful on a proxy metric, the
Governance Advisor never opines on whether something is legal, and `legal` routes anything
needing counsel to a human. The refusal is what makes a persona an advisor rather than a
generator. The eval gates that personas stay well-formed and reach the prompt; it does not grade
the writing.

## Run it

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/Tonybleything76/Agent-Team-Development.git
cd Agent-Team-Development
uv sync                      # creates .venv from the pinned uv.lock
uv run huminloop roles         # the team
uv run huminloop run "Build an AI transformation roadmap and ROI model for a manufacturer"
uv run huminloop pending       # what is waiting for a human
uv run huminloop show <run_id> # read the manifest and every artifact in the terminal
uv run huminloop render <run_id>                  # the same run as a reviewable HTML report
uv run huminloop approve <run_id> --by "Your Name"
uv run huminloop reject  <run_id> --by "Your Name" --reason "placeholder content"
uv run huminloop resynthesize <run_id>            # retry a failed Engagement Lead synthesis
```

`render` works on a **pending** run, not only an approved one: it is the page a consulting lead
reads to decide, carrying the same debate and the same Team's Plan, with the decision section
replaced by the exact `approve`/`reject` commands the run actually needs (`--force`/`--note`
included when governance requires them). Render again after deciding and the same page becomes
the record.

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

`docs/` holds three real OpenRouter runs — artifacts, plus the `manifest.json` the gate reads,
including the per-artifact SHA-256. Nothing there is a mock.

- `docs/example-run/` — the `strategy` route, before the critique loop existed.
- `docs/example-run/proposal/` — the `proposal` route, three specialists.
- `docs/example-run/critique/` — the same task as the first, run after the critique loop was
  added, with the full critique record in the manifest: the steelman, the pre-mortem, every point
  with its severity and dimension, and the author's disposition and reason for each.
- `docs/example-run/synthesis/` — all eight transformation advisors plus the Engagement Lead,
  which reads every artifact in full and reports Recommendation, Decisions, Disagreements and
  Escalations. Carries the repo's first `decision` key: approved with `--force` because three
  escalations means three questions only a human can answer.

Any of the three approved runs can be turned into the client-facing HTML report with
`uv run huminloop render <run_id>` (needs the run under `out/approved/`, not the `docs/` copy —
run one yourself or point `--root` at a directory holding the example). The page is the
"Institutional Briefing" system in `DESIGN.md`: one accent colour reserved for the human
decision, severity shown as symbol plus word rather than colour alone, no icons, no shadows.

The same task run before the Strategist persona existed produced confident benchmark figures
with no sourcing. With the persona it produces labelled assumptions:

```
[ASSUMPTION: 500 unplanned downtime hrs/yr x $8,000/hr avg cost x 25% reduction = $1.0M gross
benefit - every input must be replaced with client CMMS/finance data before this number is
cited to the CFO]
```

That rule lives in `huminloop/personas/strategist.md`, a file a human edits, not in a prompt
buried in code.

## Test it

CI (`.github/workflows/ci.yml`) runs exactly these on every push and pull request; the eval step
fails the build on any case that passed at baseline and fails now.

```bash
uv run ruff check .          # lint
uv run pytest                # unit tests: router, governance, gate, critique, orchestrator, CLI
uv run python -m evals.run   # scored eval; writes evals/results/latest.json (git-ignored),
                             # fails on regression against the committed evals/results/baseline.json
```

At v0.15.0 that is 202 tests green and no eval regression. Router exact-plan 0.957 (1.000 on the
easy regression cases, 0.913 on the deliberately ambiguous hard ones), governance verdict and issue
recall both 1.000, persona coverage 22/22, and the house brief reaching 22/22 specialists.

**Read the holdout number, not the derived one.** `transformation_route_coverage` is reported three
ways. The routing keywords were extracted from ten transformation cases, so the derived set scores
1.000 by construction — that measures nothing. Five more cases were written and held back, never
read during extraction, and those score **0.800**, which is the honest figure and the one the eval
gates on. The gap between them is the overfitting the holdout exists to expose.

## What this is not

- Not a production deployment. There is no queue, no UI, no auth; the gate is an atomic file move and a log line, on purpose.
- Not connected to tools yet. MCP server wiring from the first sketch was removed because it never worked. It stays parked: the 2026-08 review found the team was staffed wrong, and tool access would only have made a mis-staffed team faster.
- Not a claim about output quality. The dry-run provider exists to prove the control flow, not the content, and the eval is a regression harness over fixed cases — it measures that the rules do what they say, not that routing or governance is good in the wild. The eval's "hard" router cases are there to keep that honest; see the committed `evals/results/baseline.json` (and `latest.json` after you run the eval).
- The critique loop is one round, and the critic is a single role (QA/QC). It proves that structured challenge changes the deliverable; it does not prove the challenge is always right, and 100% acceptance in the committed example run is a signal to watch rather than a score.
- Two hard router cases fail and are meant to. They are reported, not hidden, and never tuned away — a hard case that always passes has stopped testing anything.
- The unit tests exercise the providers with fake clients. Real-provider behaviour is evidenced by the committed example runs, not by the test suite.

## History

First sketched August 2025 as 22 copy-pasted agent packages on the `mcp-agent` framework; the
code did not run and the repo shipped with a virtualenv and a key. Rebuilt August 2026 as one
package with the gate implemented for real.

Restaffed September 2026, and that is the more interesting revision. The roster had argued that
transformation fails for human-system reasons and then staffed twenty specialists with no change
management, adoption, readiness or workforce advisor anywhere in it — a small agency's org chart
wearing a transformation team's thesis. Six agency seats were deleted, eight advisors added, and
the routing and personas rebuilt around them. See `CHANGELOG.md`.

## Layout

```
huminloop/        package: roles, router, personas, critique, governance, llm, orchestrator, gate, storage, cli
huminloop/personas/  shared house brief + per-role markdown, edited without touching Python
tests/          pytest suite
evals/          scored eval cases + runner; results land in evals/results/
docs/           ARCHITECTURE.md — design notes; ROSTER-EVIDENCE.md — the 47 sources behind the
                roster; example-run/ — real provider output; design/ — the run-renderer reference
DESIGN.md       the visual system every rendered artifact calibrates against
```
