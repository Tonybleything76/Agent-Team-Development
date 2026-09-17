# DESIGN.md

The visual system for HuminLoop Agents' rendered run page (`huminloop render`).

## Two pivots, in order

**Pivot 1 (2026-09-03, morning): audit record → dashboard.** The original system,
"Institutional Briefing" (established 2026-08-31), was built on the premise that the rendered
page was a quiet audit record: sober, one accent color, no cards, dense serif prose. Tony's
reaction to the first real run: *"I don't know who they are... I would never even show anybody
this."* Correct and specific — the goal had become a page to run live and show people, and an
audit record is a different artifact from a dashboard. Rebuilt with stat tiles, a card-grid team
roster, color-coded severity, collapsed-by-default sections, light-by-default with an explicit
dark toggle.

**Pivot 2 (2026-09-03, same day): dashboard → narrative.** Shown the dashboard, Tony's reaction
was equally specific and equally correct: *"I don't know what the fucking shit is on the left
that I'm supposed to just scan through... This is supposed to read almost like a story of how
they began their planning."* The dashboard fixed the first problem (visual identity, readability,
color) but was still built to be *scanned*, not *read* — a persistent sidebar nav, stat tiles as
the headline, critique data reduced to badges. What was actually needed was a document: the
background, the discussion, what was cited, the pushback and why, the revision and why, in the
order it happened, ending in the plan. This is the system now — the one below.

**What survived both pivots:** the underlying data model (every specialist's draft, the critique
against it, the Engagement Lead's synthesis, the decision), WCAG 2.2 AA, `prefers-reduced-motion`,
severity as color **plus** a visible word (never color alone), the light/dark token mechanics
(bare `:root` = light, media query and `[data-theme]` override, `:not()` guard, light the default
regardless of OS setting), and a validated color palette (checked against the dataviz skill's
palette validator) rather than colors picked by eye.

## What this system is for

**The narrative report** (`huminloop render`) is what this document specifies: the rendered run
as a document to be **read start to finish**, not scanned. It answers, in order: who was
dispatched (a table of contents, not a persistent nav); what each of them concluded on their own
and why, with citations; the real pushback each one took and why; why they revised (or didn't) in
response; where they disagreed with each other; and the plan the Engagement Lead built once
everyone had finished. The ending — the human decision — comes at the end, not spoiled in the
header before any of the story has been told.

### Two surfaces, and why (added 2026-09-17)

Until v0.22.0 this section opened "One page type", and Pivot 2 below records a dashboard being
built and then deliberately reverted. v0.22.0 nonetheless shipped a second surface,
`huminloop render --dashboard`, without amending this file. The 2026-09-16 engineering review
put the contradiction to a decision rather than leaving the code and the document disagreeing.

**The decision: both surfaces stay.** They answer different questions for different moments, and
the revert in Pivot 2 was right about the question it was asked.

| | `render` | `render --dashboard` |
|---|---|---|
| Question | "What happened, and do I agree with it?" | "What do I do now?" |
| Moment | Reading the run through before deciding | A working session, often with the client present |
| Shape | One column, read top to bottom, decision last | Seven tabs, dense, everything findable without scrolling |
| Audience | The person signing their name to it | The person running the meeting |

Pivot 2 did not establish that dashboards are wrong. It established that a dashboard is the wrong
shape for *the artifact you read to decide* — the recommendation reduced to badges, the argument
reduced to stat tiles. That finding stands, and the narrative report is still the surface this
document specifies and still the default `render` produces. What v0.22.0 added is a different
artifact answering a different question, not a second attempt at the same one.

**What both surfaces owe, equally.** A render is client-facing output, so neither surface is a
lighter-weight way to show a run. Both call `render.precheck()`: the status guard (approved or
pending only — a rejected run has no settled design, see "Not yet decided") and
`gate.verify_artifacts`, which re-derives every artifact's governance verdict from the bytes on
disk. The dashboard shipped with neither, so a tampered artifact and a rejected run both rendered
clean; that is fixed, and the shared function is what keeps the two from drifting apart again.
Presentation-neutral helpers (`initials`, `pushback_rows`, `staffing`, `parse_milestones`) are
public in `render.py` and shared for the same reason — the dashboard's own `initials` had already
diverged, reading "Head of Data" as HO where the report read HD.

## Color

Validated against the dataviz skill's palette validator, not picked by eye.

| Token | Light | Dark | Use |
|---|---|---|---|
| `--page` | `#f9f9f7` | `#0d0d0d` | Page background outside cards. |
| `--surface` | `#fcfcfb` | `#1a1a19` | Card/details background. |
| `--surface-2` | `#f2f2ef` | `#212120` | Nested surface (quotes, chips, position voice). |
| `--ink` | `#0b0b0b` | `#ffffff` | Primary text. |
| `--ink-2` | `#40403c` / `#52514e` | `#d2d0c8` | Secondary prose. |
| `--muted` | `#787670` | `#a4a29a` | Labels, metadata. |
| `--rule` | `#e1e0d9` | `#2c2c2a` | Borders. |
| `--accent` | `#2a78d6` | `#5b9fed` | Links, the pending-review state. |
| `--good` | `#0ca30c` | `#39c239` | A finding that got revised; approved gate. |
| `--warning` / `--warning-ink` | `#c98500` / `#8a5a12` | `#fab219` / `#fed07a` | Disagreements, pushback, forced approval. |
| `--critical` | `#c23333` | `#f0837f` | Escalations, blocking findings. |
| `--story-wash` | `#f4f2ec` | `#221f1a` | The pushback voice block's background. |

**Status color never carries meaning alone.** Every severity badge, and every disagreement or
escalation marker, pairs its color with a visible word (`Blocking`, `Serious`, `Minor`; the
register's own name). This rule has survived both pivots unchanged.

Table-of-contents avatars use a fixed eight-color categorical order (`_TEAM_COLORS` in
`render.py`), assigned by dispatch position within a run and never reassigned — identity, not
rank.

**Theme structure.** Bare `:root` carries light. `@media (prefers-color-scheme: dark)` guarded
as `:root:not([data-theme="light"])` redefines tokens for OS-dark readers who haven't toggled.
`:root[data-theme="dark"]` redefines them again for an explicit toggle choice. A small inline
script stamps `data-theme="light"` on load unless `localStorage` says otherwise — light is the
default regardless of OS setting; a reader gets dark only by asking for it, via the toggle in
the header.

## Type

One face: Public Sans, from Google Fonts, with a real fallback stack. Body text runs larger and
looser than a typical dashboard (17px, 1.65 line-height, a ~68ch measure) — this page is meant to
be read at length, not scanned in a viewport.

## Layout — no persistent chrome

There is no sidebar and no sticky nav. The page is `.wrap`, a single centered column, top to
bottom:

1. **Header**: identity + theme toggle, an orientation paragraph describing the actual process
   (independent drafting → per-draft critique and revision → the Lead's synthesis), the task,
   and one summary sentence (bold inline numbers, severity-colored) — not a stat-tile grid.
2. **Table of contents** (`#team`): "The team involved in this planning" — every dispatched
   role, a colored initial, its remit, linked to its section below. Stated once, near the top;
   not repeated as scanning chrome against every later section.
3. **Act: "How each advisor reasoned it through."** One `<details class="story">` per advisor,
   **open by default** (this is a document to read, not a dashboard to expand piece by piece) —
   the reader can still collapse one they've finished. Each contains, in order: their position
   (prose, from Objective + Body), what they cited, the steelman, the pre-mortem, then each
   pushback finding paired immediately with the revision it produced — a `.voice.pushback` block
   directly followed by a `.voice.revision` block, so cause and effect read as a real exchange,
   not two disconnected lists a reader has to reassemble.
4. **Act: "Bringing it together."** The Team's Plan — recommendation, decisions (plain text; see
   below), disagreements, escalations, milestones, risks — plus the Engagement Lead's own
   synthesis getting challenged too (`orchestrator._do_synthesis` critiques the plan itself; the
   old system never surfaced this at all).
5. **The decision.** Once, at the close — the ending of the story, not a verdict spoiled in the
   header before any of it has been read.

## Decisions carry no "Owner" chip

The dashboard pivot rendered a Decision's owner as a bold `Owner: X` chip. Tony's reaction: *"You
put owners in there, which I'm not really even sure about."* Right to be unsure — `X` is a role
name the Engagement Lead guessed at from context, not a person who agreed to anything. It now
reads as a plain, de-emphasized note: *"A likely owner, not a confirmed one: X."* Same
information, none of the false confidence.

## Milestones, not a paragraph

The Lead's Next Steps used to render as one prose blob under "Implementation & Timeline." Broken
out now into a numbered `Milestones` list, one concrete step per item — built for someone who
wants to leave the page with a checklist, not a paragraph to re-read.

## Rules this system holds to

- **Severity is color plus a visible word**, never color alone.
- **WCAG 2.2 AA.** Body contrast ≥ 4.5:1, 44px minimum targets, reflow at 320px with no
  horizontal scroll, visible focus (`2px solid var(--accent)`, 3px offset), semantic landmarks.
- **No shadows.** Blocks separate by border and surface-color contrast, not elevation.
- **No icons and no emoji.** Team identity is a colored initial (typographic), not a pictogram.
- **`prefers-reduced-motion` respected.**
- **Light is the default, unconditionally.** Dark is opt-in via the toggle, remembered in
  `localStorage`, never silently inherited from the OS.
- **The ending is not spoiled at the top.** Anything that records a verdict — the human decision,
  in full — appears once, at the close.

**Decided (2026-09-03, v0.18.1): the model's `**bold**`/`*italic*` is interpreted, not left
literal.** A reader flagged raw asterisks in the middle of sentences — correctly; a page read as
continuous prose can't carry markup syntax as visible noise. `mdlite()` escapes everything first
(a literal `<b>` in the model's own text still can never become real HTML), then converts
`**bold**`/`*italic*` on the now-safe string. Every place rendering free-form model prose uses it.

**Decided (2026-09-03/04, v0.19.0): first-person team voice, HuminLoop brand.** Tony's reaction
to the narrative pivot's own boilerplate: *"Is it all mine? It's my team, so why are you talking
in the third person? Like I'm reading about some other account that I'm not associated with."*
Right — this page is a report from Tony's own team to Tony, not a briefing about a stranger's
engagement. Every sentence this module authors itself (not model output — advisors keep their own
"I" voice inside their own sections) now speaks as "we": "We dispatched 6 specialists," "Who we put
on this," "Our Plan," "our Engagement Lead." Tony stays "you" throughout, matching the decision
bar's voice, which was already right ("Nothing here goes anywhere until *you* read it"). Alongside
the pronoun fix, the page now carries HuminLoop's actual brand: DM Sans (headlines, labels, stat
numbers) over Inter (body prose), Deep Navy `#1a1a2e` / Body Text `#3d3d5c` ink tokens, Blue-Purple
`#7a78f5` as the primary accent, a small gradient loop-mark + "HuminLoop Agents" wordmark in the
header, and one deliberate gradient touch — a Blue-Purple → Pink-Coral border on the Recommendation
quote, the one true hero element per run, not spread across the page as wallpaper. `--muted` and
the dark-mode tokens are shaded a step darker/lighter than the brand system's literal hex to clear
AA contrast against this page's nested surfaces — documented here per the brand skill's own rule
for extending a too-restrictive palette. Status colors (good/warning/critical) are unchanged from
the narrative pivot — HuminLoop's brand system doesn't define its own, and these were already
validated. The brand system also retires HuminLoop's dark-background lockup; this page keeps its
opt-in dark toggle anyway as a deliberate, disclosed exception — an internal working document read
at all hours is a different case than a public-facing brand asset, and Tony's original objection
was to a *default* dark view, not to dark mode's existence.

Scoped out of this pass, deliberately: no attempt to auto-generate pull-quotes or "gate status"
callout cards from arbitrary advisor prose. A hand-picked callout works in a one-off mockup because
a human read that advisor's specific text; the production renderer runs over any task's arbitrary
Objective/Body content, and guessing which sentence is "the" pull-quote or which lines are
"gates" would misfire on content this module has never seen. The existing per-advisor structure —
position, citations, pushback paired with revision, risks, next steps, all inside one continuous
account — already delivers the narrative-plus-actionable-detail hybrid; it just needed the voice
and brand fix, not a new content-extraction mechanism.

## Not yet decided

- Treatment for rejected and errored-run states (unchanged across both pivots — still genuinely
  undesigned; `render_run` still refuses both with `RenderError`).
- A true live view of a run in progress — this system covers the finished (or pending) report,
  not a running one. Watching agents work in real time would need a running process pushing
  updates, not a static file generated after the fact; that's a distinct, larger feature, not
  attempted here.
