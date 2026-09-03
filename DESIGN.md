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

One page type: the rendered run, as a document to be **read start to finish**, not a dashboard to
be scanned. It answers, in order: who was dispatched (a table of contents, not a persistent
nav); what each of them concluded on their own and why, with citations; the real pushback each
one took and why; why they revised (or didn't) in response; where they disagreed with each
other; and the plan the Engagement Lead built once everyone had finished. The ending — the human
decision — comes at the end, not spoiled in the header before any of the story has been told.

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

## Not yet decided

- Treatment for rejected and errored-run states (unchanged across both pivots — still genuinely
  undesigned; `render_run` still refuses both with `RenderError`).
- Whether the model's own markdown-style emphasis (`**bold**`) in a specialist's prose should be
  interpreted or left literal. Currently literal — escaping is settled (`html.escape` on
  everything); rendering the model's own formatting choices is a bigger claim than this project
  has decided to make about text nobody has reviewed for markup, only for content. Worth
  revisiting now that the page is read as continuous prose, where literal asterisks are more
  visible than they were in the dashboard's shorter text blocks.
- A true live view of a run in progress — this system covers the finished (or pending) report,
  not a running one. Watching agents work in real time would need a running process pushing
  updates, not a static file generated after the fact; that's a distinct, larger feature, not
  attempted here.
