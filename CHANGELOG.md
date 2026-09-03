# Changelog

## 0.15.0 — 2026-09-03

Persona coverage sat at 14/22 since the roster rebuild: every transformation advisor and the two
oldest routes had a point of view, but eight real, routable specialists — `sales`,
`product_manager`, `product_developer`, `cybersecurity`, `privacy`, `hr`, `operations`, `qa_qc` —
were still falling back to a one-line remit. A team that argues transformation fails for human
reasons and then lets a third of its own roster produce generic output on exactly the tasks
where that matters (a role redesign, a data flow map, a POC's untested edge cases) has not
earned the word "trustworthy" yet.

- **All 22 specialists now have a persona.** Same house voice as the rest of the roster: first
  person, a distinct register per seat, and a `## Where I stop and ask` section that names a
  real refusal rather than a generic disclaimer — Sales won't quote a number it wasn't given
  authority to quote, Product Developer won't ship a connector that swallows its own errors,
  HR will use the words "headcount reduction" rather than laundering them into "efficiency,"
  QA/QC holds its own deliverable to the identical bar it applies as the team's critic on
  everyone else's.
- `persona_coverage` 0.636 (14/22) → **1.000 (22/22)**. Baseline re-set; no other metric moved.
- Two tests hardcoded `"hr"` as the example of "a role with no persona" — the same fragility
  the router evals already learned to avoid (a hardcoded specialist name breaks the moment the
  roster completes around it). Repointed at a synthetic role built in the test itself, so no
  future persona can retire this coverage again.
- README's Personas section and metrics still described 13 written personas and a
  `## Refuse or escalate` heading — both stale since v0.11.0's voice rewrite and this coverage
  jump. Corrected; the "13 of 22" limitation is removed from What This Is Not since it no
  longer holds.
- 183 → 202 tests, ruff clean, eval re-baselined with no regression (h05 and t12 remain the two
  expected hard-case failures).

## 0.14.0 — 2026-09-02

The rendered page buried the one thing a reader actually needs — what the team decided, and
what it needs from you — after sixteen sections of per-advisor detail. And it silently dropped
the Engagement Lead's own Next Steps and Risks sections entirely: real implementation timeline
content, generated every run, never once rendered.

- **The Team's Plan now leads the page**, immediately after the header — Recommendation,
  Decisions, Disagreements, Escalations — before any per-advisor Critique or Artifact section.
  Everything below it is now explicitly framed, in the page's own copy and nav grouping, as
  supporting detail: "how the team got there."
- **Implementation & Timeline and What Could Go Wrong are new sections** inside the plan,
  pulled from the Engagement Lead's own Next Steps and Risks — content the artifact always
  contained and the renderer never surfaced.
- **Disagreements and Escalations carry a one-line explainer** of what they are, since "the Lead
  had to weigh conflicting advisor conclusions" reads clearer cold than the register name alone.
- Nav reorganized to match: "Start here" (the plan) above "How the team got there" (routing and
  every advisor's critique/artifact), rather than one flat list.

## 0.13.1 — 2026-09-02

The healthcare example run's task happened to end in a clean short question, so the headline
split looked settled. The next real task didn't — a dense scenario brief with no sentence under
30 words and no trailing "?" — and `split_headline` dutifully forced that whole sentence into
the 22ch display-type column anyway, wrapping ten lines of giant serif type. The exact
"scrunched" failure the split was built to fix, just from a different cause.

- **`split_headline` now refuses to fake pithiness.** Past `PITHY_MAX_CHARS` (90), no candidate
  sentence counts as a real headline — the caller falls back to a `"The task"` quote block
  holding the task verbatim, at prose size, rather than force-fitting the wrong sentence into
  display type. Still never paraphrases: the fallback is a rendering choice, not new text.

## 0.13.0 — 2026-09-02

Milestone 2: the run renderer. `DESIGN.md` and the approved reference implementation existed
since 2026-08-31; this is the Python that actually produces the page from a real run instead of
a hand-authored mock of one.

- **`huminloop render <run_id>`** turns an approved run into a single self-contained HTML file:
  the header, the run-flow strip, the decision bar (including the forced/amber state), a sticky
  index scaled to however many advisors actually ran, each specialist's Critique and Artifact
  sections, and — new, since no prior version of this page ever had one — the Engagement Lead's
  Recommendation, Decisions, Disagreements, and Escalations as their own Synthesis section.
  Refuses to render anything but an approved run, and re-verifies every artifact's SHA-256
  before rendering — a run whose bytes changed after the decision was recorded is not rendered,
  the same rule the approval gate already holds itself to.
- **The Engagement Lead's `Escalations` register was reporting the wrong count.** `parse_registers`
  captured each register's body up to the next `##` heading or end of string, but Escalations
  is always the last of the four registers and sits inside the outer envelope's plain `Body:`
  section — with no more `##` headings coming, its capture ran straight through `Citations:`,
  `Risks:`, and `Next Steps:`, silently absorbing Next Steps' own numbered lines as escalations.
  The already-committed example run's manifest said 7 for exactly this reason; the real number,
  and what the artifact's own text has always said, is 3. Fixed, and corrected in the committed
  example — the approval note, the process flags, and the synthesis counts, not the artifact
  text itself, which was never wrong.
- Task headlines that are a full scenario-plus-question paragraph (real ones, not the reference's
  eleven-word original) now split at the task's own trailing question rather than wrapping a
  paragraph into display type — the split is structural, not a paraphrase: nothing reworded,
  nothing invented.

## 0.12.0 — 2026-09-02

The first real proof run's Engagement Lead came back empty. Not truncated — empty:
`finish_reason=length` with zero visible text. Eight advisors had already succeeded, ~$0.80
spent, and the one deliverable the client acts on was gone.

The cause was a shared assumption: every call, specialist or supervisor, budgeted the same
6000 tokens. That's enough for a single 700-word memo. It is not enough for a call that reads
eight of those memos in full — up to 40KB of context on a loaded task — and integrates them
into four registers. The model was spending the whole budget before any answer reached the
response.

- **Token budgets are now tier-aware.** `resolve_max_tokens(role)` gives a supervisor role
  (today, only the Engagement Lead reaches the model) 16,000 tokens by default instead of a
  specialist's 6000 — `LLM_MAX_TOKENS_<ROLE>` or `LLM_MAX_TOKENS` still overrides either.
- **An empty completion now says why.** "openrouter returned an empty completion" told a
  reviewer nothing about whether the cause was the token cap or something else entirely. It now
  names the budget that was spent and which finish/stop reason triggered it, only when that's
  actually what happened — a content-filtered empty response still gets the plain message,
  because there's no cap to blame there.
- **`huminloop resynthesize <run_id>`** retries only the Engagement Lead against a pending run's
  artifacts already on disk. A failed synthesis after twenty-four paid specialist calls used to
  mean paying for all twenty-four again to get a second attempt at the one call that failed.
  Refuses to touch a run that isn't pending, is still owned by a live process, or already has a
  successful synthesis — this is a retry, not a way to overwrite a finished one.

Resynthesizing the actual proof run cost about $0.12 and worked: two genuine disagreements
among the eight advisors, six decisions, seven escalations. The advisors did not agree on
everything, which is what "read the Disagreements register before you trust it" was for.

## 0.11.0 — 2026-09-02

The team sounds like a team now. This is a voice change, and it is a correctness change.

The system argued that AI transformation fails for human reasons, then talked to its own
advisors the way a bad manager talks to a junior. Every persona ended in a section headed
**"Refuse or escalate"** — a list of prohibitions, every line starting "Do not". Nobody was ever
invited to be uncertain, asked anything, or told it was safe to be wrong. A system built to
demonstrate psychological safety that models none of it is not making its own argument.

- **`## Refuse or escalate` is now `## Where I stop and ask`**, across all fifteen personas and
  the eval gate, in one change. Same boundaries. A practitioner naming their limits instead of a
  system issuing rules. "I will not sign a readiness assessment built only from what managers
  said about their teams. That tells us what managers believe, which is a genuinely useful and
  completely different fact. Let me talk to the people who will actually do the work."
- **All fifteen personas rewritten for voice, and given distinct registers.** The Domain Owner is
  impatient with abstraction. The Value Realization Lead is dry and allergic to unfalsifiable
  claims. The Change Management Lead asks a lot of questions. The Data Readiness Lead is literal
  and unglamorous about it. They should not read as one narrator wearing fifteen hats.
- **The house brief gained what it was missing: permission to be uncertain.** It demanded rigour
  and human impact but never said it was safe to say "I do not know." Now it says so explicitly,
  with examples, because the version most teams have is aspirational and this one needs to be
  operational.

**Two frameworks are now load-bearing rather than decorative.**

Edmondson's **teaming and psychological safety**: the work is framed as a learning problem
rather than an execution problem, updating your position is what the work is for, and the most
expensive silences are the ones where somebody knew.

Schein's **humble inquiry**: ask before you tell. The question you were handed is usually
sitting on top of the real one, and asking what the client is actually trying to change is
frequently the advice rather than the preamble to it.

**De Bono's six hats** are now the shared vocabulary for scrutinizing a plan, because
disagreement stops feeling personal the moment it is a mode rather than a verdict. Saying
"putting the black hat on for a moment" makes a hard objection land as a contribution. The
Engagement Lead also watches the distribution: eight advisors wearing yellow have produced a
brochure, and eight wearing black have produced a reason to do nothing.

The renderer copy was rewritten to match. "A governed agent team. Specialists draft, a critic
challenges every draft on the record, rule-based governance checks each artifact" became "A team
of AI advisors that argues with itself on purpose. Each one drafts, a critic pushes back on the
record, and nothing goes out until a person reads it and puts their name on it."

169 tests, ruff clean, no eval regression. `techno-social` stays in the house brief — it is the
project's own framing language and a test pins it.

## 0.10.0 — 2026-09-02

The team is hierarchical now. Before this it was a flat pipeline calling itself one.

`orchestrator.run()` dispatched N specialists in sequence, each seeing 600 characters of its
predecessors, and stopped. The two SUPERVISOR-tier roles were not agents: `router` is a keyword
function and `governance` is a rule-based checker. Ask the team a real question and six advisors
produced six disconnected memos and nobody answered it. The operator did the integration in his
own head, which is the work the team exists to do.

- **`engagement_lead`** — a SUPERVISOR-tier role dispatched after every specialist through a new
  `synthesize()`. It reads every artifact **in full**, not the 600-character window specialists
  get, plus each artifact's governance verdict and any unresolved blocking critique. It produces
  the one document the client acts on.
- **It does not call `produce()`.** That function raises on any role outside `SPECIALISTS`, and
  the guard keeps holding so the router and the governance evaluator can never be dispatched as
  peers. A test asserts it still raises for every supervisor, the lead included.
- **Four registers, parseable from the bytes.** Recommendation, Decisions (each ending `-> role`),
  Disagreements, Escalations. `parse_registers()` is regex over headings, so the counts the CLI
  and the gate rely on never require a model call. An empty register must say "None." — absence
  and emptiness must not look the same to a reader.
- **Escalations reach the gate.** Each becomes a `process_flag` on the synthesis artifact, so
  `flagged_roles()` picks it up and releasing the run needs `--force` plus a written note. A
  question only the human can answer now costs a human their signature.
- **The lead is governed and critiqued like everything else.** No exemptions for the supervisor.

**The failure this was built to prevent** is a synthesis agent that reads six advisors, finds
real conflict, and writes "the team recommends a phased approach." The persona refuses
manufactured consensus in those words, and `tests/test_synthesis.py` asserts the pipeline gives
the lead everything needed to see a conflict: both artifacts in full, unresolved blocking
critique, and the names of seats that produced nothing. What those tests deliberately do **not**
claim is that a real model names a conflict it was shown — that is a property of the model, and
the committed example run is the evidence. Tests claiming otherwise would be theatre.

**Personas now carry the operator's actual practice, not generic competence.**

- `change_management_lead` works **ADKAR** explicitly and names it. Awareness, Desire, Knowledge,
  Ability, Reinforcement — sequential and diagnostic, so a person stuck at Desire is not fixed
  with more training. It previously used the word "reinforcement" without ever naming the model
  it comes from.
- `ld` is **new** and works **Jane Vella's 4-I model**: Inductive, Input, Implementation,
  Integration, with Structure, Support and Challenge in balance. It was a dispatchable specialist
  with no persona at all.

`persona_coverage` 0.591 → 0.636 (14/22). The metric now counts **specialist** personas only:
the lead's persona is reported as `supervisor_personas_written` rather than inflating a numerator
against a specialist denominator.

**Edge cases, all handled and none silent.** Zero successful specialists means no synthesis and a
logged `synthesis_skipped`. A single artifact still synthesizes, because one voice still needs a
decision register. Errored seats are named to the lead as an absence it must declare. A failed
synthesis is recorded like a specialist error and never costs the advisors' completed work.

169 tests, ruff clean, eval re-baselined with no regression.

## 0.9.0 — 2026-09-01

The eight transformation advisors have personas. They were reachable in v0.8.0 but still ran on a
one-line remit, which produces confident generic output — the failure that lost trust in this team
in the first place. Milestone 1b closes that.

- **Eight personas written**: `domain_owner`, `value_realization_lead`, `change_management_lead`,
  `process_excellence_lead`, `data_readiness_lead`, `enterprise_architect`,
  `program_management_lead`, `governance_advisor`. `personas_written` 5 → 13,
  `persona_coverage` 0.227 → **0.591**. The nine specialists still without one are support and
  delivery seats the roster inherited, not the advisors this rebuild was for.
- **`## Refuse or escalate` is now gated.** `PERSONA_SECTIONS` was `("## Remit",
  "## Output contract")`; the refusal section is the one that makes a specialist an advisor
  rather than a generator, and it is the easiest to drop when writing eight personas in one
  sitting. All five existing personas already carried it, so this cost nothing and prevents the
  regression it was added for.

**Each persona names what it will not do, and the refusals have teeth.** The Value Realization
Lead will not mark a benefit realized on a pilot's own instrumentation, and will not convert freed
hours into cash without a named person committing to the decision. The Change Lead will not sign a
readiness assessment built only from management self-report, and publishes its delay gate before
anyone is under pressure. The Process Lead will not deliver a happy-path map or place a checkpoint
where the reviewer lacks the evidence to judge. The Data Readiness Lead withholds approval on any
dataset whose lawful basis for training cannot be established. The Governance Advisor will not
issue a conditional approval worded so it reads as approval.

**Overlap was designed against, not left to chance.** `value_realization_lead`, `data_scientist`
and `finance` all touch baselines and ROI, so each now states its boundary: the Data Scientist
designs the measurement, Finance checks a single case's arithmetic, and Value Realization owns the
portfolio ledger and the scale-or-stop decision. The Governance Advisor's persona explicitly
distinguishes it from the automated `governance` evaluator — that one checks bytes, this one
decides whether a system should exist.

**A local-tooling bug in `persona_keys()` is fixed.** It globbed `*.md` and turned any stray file
into a phantom role, so a gitignored `domain_owner.plain.md` sibling written by local tooling
crashed the eval with `KeyError: 'domain_owner.plain'`. It now returns only stems that name a real
role. Because silently skipping a file could hide a misspelled persona that loads for nobody,
`tests/test_personas.py` fails loudly on any non-sibling file that does not name a known role.

**The proof task was rewritten and dry-run, not paid for.** The old task fired zero routing rules
and would have produced one Strategist memo proving nothing. The rewritten task (in `TODOS.md`)
fires six rules and dispatches six advisors — 18 LLM calls against the 21-call worst case already
measured — and reaches adoption, process and program management, which the plan set as the bar.
Verified offline as run `20260901_144930_dd8b92`. **The paid run is still unspent and is a human
decision.**

Eval re-baselined at v0.9.0; `h05` and `t12` remain recorded known failures and the holdout still
reads 0.800. 158 tests, ruff clean.

## 0.8.0 — 2026-09-01

The eight transformation advisors are now reachable. v0.7.0 seated them and routed nothing to
them, which is the worse of the two failure modes: a roster that implies a capability the system
cannot dispatch.

**Eval cases were written before the routing rules, and five were held back.** Fifteen
transformation questions in client language went into `evals/cases.json` tagged
`"category": "transformation"`. Routing vocabulary was derived from ten of them plus the advisors'
own remits; the five tagged `"holdout": true` were not read during extraction. That ordering is
the whole method — deriving keywords from the cases you then measure against tests only that you
can copy words between two files.

- **Eight routing rules added** (`domain_ownership`, `value_realization`, `change_adoption`,
  `process_design`, `data_readiness`, `architecture`, `program_delivery`, `ai_governance`), one
  per advisor. The router goes from 13 rules to 21. They sit between `strategy` and `proposal`,
  ordered by engagement logic rather than alphabetically, because a task matching two rules
  dispatches in `ROUTING_RULES` order: who owns the outcome, what it is worth, who absorbs the
  change, how the work is done, then data, architecture, delivery and assurance.
- **`transformation_route_coverage` added**, reported three ways: whole, derived, holdout. It
  asserts each case's full ordered plan against `expect_roles`, not "contains an advisor" — a
  contains-any check would be satisfied by one broad keyword while the first role is wrong. Rates
  are `hits / max(n, 1)`, so an empty tagged set reads **0.0 and fails**, never a vacuous 1.0.
- **The holdout is gated at 0.80** and checked before the baseline branch, so a below-gate result
  cannot be recorded as the new normal.

**The numbers, with the asterisk they need.** `transformation_route_coverage_derived` is **1.000**
and that is by construction, not evidence — the vocabulary was written from those ten cases.
The number that means anything is `transformation_route_coverage_holdout` at **0.800**, four of
five, against language the keyword list had not seen.

**`t12` is a recorded miss, not a fixed one.** The client says *"can we still train a model on
this?"*; the vocabulary derived from `t04` says `fine-tune` and `training data`. Adding
`train a model` after seeing `t12` fail would be copying words between two files and would have
reported 1.000 with no way to tell the difference. One honest vocabulary pass was run, not two;
the second is still available if coverage needs to move, and the decision trigger stands — if the
holdout cannot reach 0.80 after two honest passes, keyword routing has hit its ceiling and
semantic routing is back in scope with evidence.

**`h05` is a real ambiguity again.** The old case tested an EA-versus-cybersecurity ambiguity that
deleting `ea` voided in v0.7.0, so it passed mechanically and held
`router_hard_exact_rate` at a fake 1.000. It is replaced by an ambiguity this release
introduces: `pilot` is the transformation term for a scoped first deployment and also the ordinary
word for a first cut of a script, so "Draft the pilot script for the new onboarding training
video" pulls in `value_realization_lead` alongside `hr` and `ld`. Recorded as a known failure,
which prices the broadest new keyword honestly. `router_hard_exact_rate` now reads **0.913** over
23 hard cases — down from 1.000, and the lower number is the truthful one.

**A default plan now flags the artifact it produced.** `Plan.used_default` was read only by a
test. When no routing rule matches, the artifact the fallback Strategist produced carries a
`process_flag` saying the specialist was dispatched on a guess. `process_flags` is artifact-level
and `flagged_roles()` iterates artifacts, so a plan-level field would never have reached the gate.
**This is a behaviour change:** an unroutable task now requires a human's `--force` to approve,
where before it produced a confident, governance-clean memo about the wrong thing and passed
silently.

**Counts held, guards armed.** `router_cases` 32 → 47, `router_easy_cases` unchanged at 24,
`router_hard_cases` 8 → 23. No case was deleted. `GATED_COUNTS` is untouched; the two new count
guards (`transformation_cases`, `transformation_holdout_cases`) live in a separate
`TRANSFORMATION_GATED_COUNTS` checked alongside it, because deleting the *failing* tagged cases
would otherwise raise coverage rather than lower it.

**Still interim.** The advisors route now, but their personas are not written, so they will
produce generic output — the same failure that lost trust in the first place. Personas are the
next piece of work. Do not spend on a live proof run before then.

Eval re-baselined deliberately at v0.8.0 with `h05` and `t12` recorded as known failures. 152
tests, ruff clean.

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
