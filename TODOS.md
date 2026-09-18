# TODOS

## Phase 4 — the paid proof run

**Status: DONE.** Spent, reviewed, approved, and committed as evidence — then spent several more
times to build and shake out the run renderer.

The healthcare claims-copilot task (unchanged since v0.9.0) has now run against the live
OpenRouter provider at least five times. The first, `20260902_044655_a29747`, is the one that
matters for the record: all eight advisors plus the Engagement Lead completed (~$0.80), Tony
reviewed the voice and the synthesis, approved it with `huminloop approve ... --force --note
"..."` (forced because 7 escalation-derived process flags require a note), and it's committed at
`docs/example-run/synthesis/` as the first synthesis example with a `decision` key.

That first run also surfaced a real bug: `parse_registers`'s Escalations capture ran past its own
register boundary into Citations/Risks/Next Steps, so the manifest recorded 7 escalations where
the artifact text only ever supported 3. Fixed in v0.13.0; the committed example's manifest,
approval note, and process flags were corrected to match (the artifact text itself was never
wrong).

Four further runs (`proof3`–`proof5` under this job's tmp dir, local scratch only — not
committed) exercised the full 9-role plan (all eight advisors + `ld`), used to build and verify
`huminloop render` against real output rather than a hand-authored mock. One of those runs is
what caught the Escalations bug above.

**Reference for anyone re-running it:** `LLM_PROVIDER=dryrun uv run huminloop run "<task>"` still
verifies routing/plan shape for free before spending on the live provider.


## Re-resolve the citation URLs in docs/ROSTER-EVIDENCE.md

**Status: DONE (2026-09-02).** All 47 Vertex AI Search redirects replaced with the canonical
publisher URL each one resolves to, verified live (bcg.com, mckinsey.com, medium.com, and
researchgate.net block plain automated fetches — those four were confirmed live by other means,
noted in the doc's header rather than treated as broken). Four Accenture citations [17, 18, 21,
26] resolved to generic careers-search pages rather than the original specific job posting —
correctly attributed, just a landing page instead of one exact requisition; also noted in the
header. Nothing left to do here.

## Engagements

### Per-role context scoping

**What:** Let a context file declare which roles may read it, instead of broadcasting all of
`context/` to every dispatched advisor.

**Why:** Data minimization, separate from token cost. A discovery transcript with named
employees goes to every seat on the run, not just the seats that need it.

**Context:** `orchestrator.py:346` reads context once and hands the same block to every role at
`:381-383`. Candidate shapes: front-matter key in the file, a subdirectory per role, or a naming
convention — none obviously right yet, so this needs a design pass rather than a patch. Raised
by the Codex outside voice during the 2026-09-16 eng review of v0.22.0.

**Effort:** M
**Priority:** P2
**Depends on:** the context clearance prompt (eng review Issue 2A) and the per-run context
snapshot (Issue 17B).

### Engagement context does not influence staffing

**What:** Let engagement context participate in routing, or warn when it clearly should have.

**Why:** A task like "what should we do next?" inside a healthcare engagement whose `context/`
is full of HIPAA material still routes to the default Strategist, with no governance or legal
seat. The staffing note then honestly reports "no rule matched this task" — correct and useless.

**Context:** `orchestrator.py:345-346` calls `router.route(task)` first and `load_context`
second; routing decides the team before anything knows what the engagement is about. The
`brief` field in `engagement.json` is also unused by routing and is the cheapest first move.
The hard part is preserving the router's determinism, which is a tested property
(`test_router.py`) and deliberately chosen. Raised by the Codex outside voice, 2026-09-16.

**Effort:** M
**Priority:** P2
**Depends on:** benefits from `status --json` landing first so staffing rationale has one home.

### Permissions, retention and close-out for client material

**What:** Decide how long client material lives in `~/Cowork/Engagements`, who can read it, and
how an engagement gets closed out.

**Why:** Transcripts land under the home directory with whatever umask gave them, no expiry, no
archive path, no delete command. For a consultancy this is a contractual question, not a
tidiness one — and the per-run context snapshot multiplies the copies.

**Context:** `engagement.py:77-78` creates the tree with a plain
`mkdir(parents=True, exist_ok=True)`. `engagement.json` already carries `"status": "active"`,
which nothing reads or changes — a half-built hook for exactly this. Cheapest useful version:
restrictive mode at creation, an `engagement close` that flips `status` and optionally purges
`context/`, and a stated retention posture in the generated `CLAUDE.md`. Do this before a
second real client goes into the system. Raised by the Codex outside voice, 2026-09-16.

**Effort:** M
**Priority:** P2
**Depends on:** the per-run context snapshot (Issue 17B) and the clearance record (T2A).

### The narrative report never says what the team was given

**What:** `huminloop render` (the default surface) does not show `context_read`. Only
`render --dashboard` does.

**Why:** The `context/README.md` that `engagement new` writes into every engagement promises,
in those words: "Every run's report states which of these the team actually read, so you never
have to guess whether the thing you added made it in." The default report does not keep that
promise, so the guarantee holds only if you happen to pass `--dashboard`. This is the same
silent-omission shape the 2026-09-16 review was about, one layer up: the record exists in the
manifest and the page simply does not print it.

**Context:** `render.py` has no reference to `context_read` at all (grep returns 0);
`dashboard.py:178` is the only consumer. Pre-existing since v0.22.0, not introduced by the
eng-review branch — found by that branch's own pre-landing review. The fix is a small section in
`render_run`, mirroring the dashboard's chip row, including the refused/unreadable/empty states.

**Effort:** S
**Priority:** P1

## Gate integrity: the manifest certifies itself

Three `/ship` review rounds on `fix-tampered-run-dead-end` (v0.23.1) kept finding new
hand-edits of `manifest.json` that the gate trusts. The root cause is one design fact: the
digest, the review verdict and the list of artifacts that verification checks all live in the
same file an attacker edits. Patching each edit does not converge. The fix is to anchor what a
run produced somewhere the manifest cannot rewrite, such as an append-only log written at run
time and checked by `verify_artifacts`. These are the reproduced cases it must close.

### Recomputing digests inside the manifest defeats the byte check
Replace an artifact's bytes, write `sha256_text(new)` and `review_text(new).ok` into the
manifest, and `status` says approve and `approve` succeeds with no trace. **Priority:** P1

### A duplicate-role entry can point approval at bytes the page never showed
`render_run` keys texts by role, so a second entry with the same role and a matching digest is
verified and approved but never displayed. **Priority:** P1

### Deleting a flagged artifact entry removes its flag
Only listed entries are verified and flagged; the file stays on disk unchecked. The same holds
for stripping `process_flags`. **Priority:** P1

### A hand-written recorded approval skips the flag check
`_decide` completes a recorded decision without re-running the `--force` check; the approver it
records is whoever the manifest names. **Priority:** P1

### Reject then reopen clears the interrupted marker
`reopen` sets `status` to `pending`, so an interrupted run, once rejected and reopened, is
recommended for and accepts `approve`. On main before v0.23.1. **Priority:** P1

### A hard crash between claim and write leaves the claim file
Exceptions now remove it; a kill or power loss still leaves `.deciding` or `.superseding`, and
every later decision is refused until it is deleted by hand. **Priority:** P2

## Deferred from the 2026-09-17 pre-landing review

These were found by `/ship`'s own review of the eng-review branch and deliberately not fixed
there — each needs a design decision rather than a patch. The three CRITICALs that branch did
fix (the `resynthesize` clearance bypass, the cross-fence forgery, and a blank over-budget file
producing a false audit record) are done; these are what is left.

### A hard link defeats the context containment check

**What:** `engagement._within()` refuses a symlink out of the engagement but not a hard link.
Reproduced: `ln /outside/leak.md <eng>/context/hard.md` yields
`{'file': 'hard.md', 'chars': 21, 'state': 'read'}` and the outside file's bytes in the block,
with no `resolves_to` — the audit record is actively misleading.

**Why not fixed now:** `path.resolve()` has nothing to resolve for a hard link, so the fix is a
different mechanism (`os.open` with `O_NOFOLLOW`, then `fstat` and refuse `st_nlink > 1`), and
that also refuses legitimately hard-linked files. It needs a decision about which it would
rather be wrong about. Lower practical risk than the symlink case: it needs local write access
to a folder a human curates, and the same filesystem.

**Effort:** M
**Priority:** P1

### TOCTOU between the containment check and the read

**What:** `_within()` resolves the path, then `path.open()` re-traverses it; a symlink swapped
in between is followed. Separately `context_files()` calls `p.is_file()` and `p.stat()` on
unvalidated paths before containment is considered, so an out-of-tree target's existence and
mtime leak into the ordering even for files later refused.

**Why not fixed now:** the honest fix is to open once and validate the descriptor
(`os.open(..., O_NOFOLLOW)` + `fstat`, read from that same fd), which restructures
`load_context`'s whole read path. Same low practical risk as the hard link.

**Effort:** M
**Priority:** P2

### The fence defuses only byte-identical markers

**What:** `governance.fenced()` now neutralises every known marker (and the neutralised token
itself), but only exact matches. A near-miss (`----` one dash short), a case variant, or a
unicode-lookalike dash still reads to a model as a boundary while failing the string compare.
Nothing normalises the body first, so zero-width and bidi characters can be interleaved to
evade the replace while still rendering as the marker.

**Why not fixed now:** the fix is normalisation (NFKC + `strip_controls` + a run-length-tolerant
regex), which changes what reaches the model and needs its own eval cases before it lands.

**Effort:** M
**Priority:** P1

### The recorded clearance identity is unauthenticated

**What:** `context_clearance["by"]` comes from `--cleared-by` (arbitrary text) or
`getpass.getuser()`, which reads `LOGNAME`/`USER` before the password database — so
`USER=ceo huminloop run ...` records `"by": "ceo"`. The manifest presents that next to a real
sha256 and timestamp, which implies more than it can support.

**Why not fixed now:** `gate.py` already states the project does not authenticate the human
(single-operator CLI), so this is a consistency and honesty question across both records, not a
clearance-only patch. Cheapest useful version: record `identity_source`, prefer
`pwd.getpwuid(os.getuid()).pw_name` as the fallback, and say plainly in `show` output that the
name is self-asserted.

**Effort:** S
**Priority:** P1

### The manifest stores absolute paths that identify the operator

**What:** `context_clearance["source_dir"]` and a refused file's `resolves_to` are absolute
paths. `resolves_to` by design records where a refused file pointed — potentially another
client's document, e.g. `/Users/<name>/Cowork/Engagements/<other-client>/...` — and this repo
commits example runs (`docs/example-run/`, now `tests/fixtures/`).

**Why not fixed now:** it needs a redaction policy, which is the same decision as the retention
and close-out item above. Do them together.

**Effort:** M
**Priority:** P1

### Maintainability follow-ups

Sixteen informational findings, none blocking. The ones worth doing first: `gate._decide()` still
inlines `("running", "incomplete")` instead of the `INTERRUPTED_STATUSES` constant added beside
it; `ESCALATION_PREFIX` and its scan exist in `dashboard.py`, `server.py` and `orchestrator.py`
as three copies; `gate.list_runs()` invents status strings outside the new `RUN_STATUSES`
vocabulary, so `pending` still reports statuses no caller of `status --json` can match; and
`CRITIC_ROLE`/`SYNTHESIS_ROLE` would sit better in `roles.py` than in `orchestrator.py`, which
currently makes the approval gate depend on the whole run engine for two strings.

**Effort:** M
**Priority:** P2

### Deferred from the adversarial re-review (2026-09-17)

Three findings against the pre-landing fixes themselves. The five defects that pass found are
fixed; these need a decision.

**The clearance record certifies itself.** `cleared_snapshot` checks the snapshot against a
sha256 stored in the same `manifest.json` that whoever edited the snapshot also controls, and
`gate.verify_artifacts` covers only `manifest["artifacts"]` — never `context_clearance`,
`context_read`, or `out/<run>/context/context.md`. Reproduced: rewrite the snapshot, rewrite
the hash, and the material is served still attributed to the original approver. The clearance
also carries no `run_id`, so it is portable between runs. Fixing it properly means binding the
clearance to the run, extending `verify_artifacts` to cover the snapshot, and writing the
clearance into `logs/runs.jsonl`, which is the one append-only record here.
**Effort:** M  **Priority:** P1

**The audit record keys on basenames.** `context_files()` enumerates with `rglob`, but every
row records `path.name`, so `context/notes.md` and `context/sub/notes.md` are indistinguishable
in `context_read`, in `clearance["files"]`, in the consent prompt, on the dashboard chips, and
in the `### notes.md` headers the model reads. A refused file can share a basename with a file
that was read. The fix is to record the path relative to `context/`, which also touches the
eval's unrecorded-files check.
**Effort:** S  **Priority:** P1

**Nothing surfaces the clearance.** It is written to the manifest and justified as existing so
it can be proven later, but no reader shows it: not the report, not the dashboard, not
`status`. Only `show`'s raw JSON dump exposes it. A human approving a run cannot see who
cleared the client material it was built from, while both surfaces do show the unverified
`context_read` chips.
**Effort:** S  **Priority:** P1

### Deferred from the third adversarial round (2026-09-17)

Round 3 reviewed round 2's fixes and found ten issues. Five were fixed; these five were not,
and the 0.23.0 CHANGELOG now states each as a limit of the clearance gate rather than leaving
it to be discovered.

**`is_cleared` proves the bytes, not the human.** It checks `sha256` and `files` and ignores
`by`, `at`, `method`, `bytes` and `source_dir`, all of which are written into the manifest as
the permanent record. A clearance of `{"by": "", "at": "not-a-time", "method": "I made this
up", "source_dir": "/somewhere/else"}` with a correct hash passes the gate and is recorded
verbatim. Fix: require a non-empty `by`, a parseable `at`, a `method` from a known set, and
`bytes`/`source_dir` consistent with the block. **Effort:** S **Priority:** P1

**The two doors still differ on the file list.** `run()` uses `is_cleared` (sha256 + files);
`resynthesize` uses `cleared_snapshot` (sha256 only), so a clearance naming entirely different
files is accepted on the recovery path and rewritten into the manifest as the standing record.
Fix: have `cleared_snapshot` reconstruct the predicate from the snapshot plus `context_read`
and call `is_cleared`. **Effort:** S **Priority:** P1

**`FENCE_NOTICE_FORGED` is itself never defused.** The identity no-op was moved rather than
eliminated: a document can plant the terminal token and assert, in the system's own vocabulary,
that a notice was found. Lower impact than the original (the forged claim is weaker) but the
same unbounded shape. Fix: one idempotent self-describing token, or a per-run nonce so a
planted copy never matches the emitted one. **Effort:** S **Priority:** P2

**`_contained` reports every resolve failure as `unresolvable`.** A symlink loop or a target
behind an unreadable directory that points outside the engagement now reads as benign
housekeeping, and the reviewer loses the target path. Neither can leak (the open fails), so
this is presentation. Fix: distinguish ENOENT from ELOOP/EACCES and keep `resolves_to` for the
latter. **Effort:** S **Priority:** P2

**Two weak assertions survive.** `tests/test_engagement.py`'s blank-file budget tests still
pass with `_overflows` reverted to `len(chunk) > remaining`; they cover the blank-file branch
correctly but do not pin the overflow logic. Only
`test_a_short_file_with_a_long_blank_tail_is_not_called_truncated` does.
**Effort:** S **Priority:** P2
