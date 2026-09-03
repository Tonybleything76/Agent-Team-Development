# DESIGN.md

The visual system for HuminLoop Agents. Established 2026-08-31 in `/plan-design-review`,
from the approved run-renderer direction ("Institutional Briefing"). Reference implementation:
`.design-work/run-renderer-reference.html`, published at
`https://claude.ai/code/artifact/e00eca97-74d0-4c1a-83d8-5b86ff458d13`.

This is the first visual standard in the project. Before it, the repo had no CSS, no HTML and no
design decisions of any kind. Everything visual calibrates against this file.

## What this system is for

One page type: the rendered run. A document that has to work for two readers at once — a hiring
manager giving it ninety seconds who never scrolls past the fold, and the operator reading it end
to end to consult the advisory team on live client work.

It is an **audit record**, not a landing page and not a dashboard. Authority comes from sobriety.
Nothing decorative earns its place; every visual device encodes something true about the run.

## Color

Neutrals carry a slight green bias so they read as chosen rather than inherited. One accent, used
sparingly, reserved for the human decision — the thing the project exists to prove.

| Token | Light | Dark | Use |
|---|---|---|---|
| `--ground` | `#fcfcfb` | `#131615` | Page background. Always set explicitly on `body`. |
| `--panel` | `#f4f6f5` | `#1a1e1c` | Steelman and pre-mortem blocks. |
| `--ink` | `#181a19` | `#e9ece9` | Primary text. |
| `--ink-2` | `#3d443f` | `#c2c8c3` | Secondary prose, author responses. |
| `--muted` | `#6e756f` | `#8d948e` | Labels, metadata. |
| `--faint` | `#9aa19b` | `#6a716b` | Numerals, disclosure markers. |
| `--rule` | `#dfe2e0` | `#2a302c` | Structural rules. |
| `--rule-soft` | `#eaedeb` | `#212623` | Between findings. |
| `--accent` | `#1d5240` | `#78c3a0` | The decision, and only the decision. |
| `--accent-ink` | `#123528` | `#9fd8bb` | Accent text needing AA contrast. |
| `--accent-wash` | `#eef3f0` | `#18231e` | Decision bar ground. |

**Theme structure is load-bearing.** The bare `:root` carries the complete light palette.
`@media (prefers-color-scheme: dark)` guarded as `:root:not([data-theme="light"])` redefines
**only tokens**. `:root[data-theme="dark"]` redefines them again. No color may be declared only
inside a media or `[data-theme]` block — that is the classic unreadable-page bug.

**Semantic color is separate from the accent.** A forced approval uses `#8a5a12` (amber), never
the green. Severity never uses color as its only signal.

## Type

Two faces, both from Google Fonts, with real fallback stacks.

- **Spectral** (300/400) — the task headline, steelman and pre-mortem prose, author names,
  decision notes. Anything meant to be read rather than scanned.
- **Public Sans** (400/500/600/700) — structure, labels, metadata, findings, navigation.
- **`ui-monospace`** — hashes, `out/pending/`, severity glyphs only.

Scale: task headline `clamp(28px, 4.4vw, 42px)` at weight 300, `-.015em`, `text-wrap: balance`,
max 22ch. Section heads 26px Spectral 400. Body 16px/1.7. Prose blocks 17px Spectral 300.
Labels 10-11px, `.16em`-`.2em` tracking, uppercase, weight 700.

Running text stays near 65-74ch. `font-variant-numeric: tabular-nums` on every column of digits.

## Layout

Sticky index left (190px), content right, 56px gap, collapsing to a horizontal scroller under
880px. Prose holds a measured column rather than filling the viewport. Flex and grid with `gap`
throughout — never per-element margins.

Header order, decided deliberately: product identity, orientation sentence, task headline, run-flow
strip, decision bar. The decision appears **twice** — once in the header so a ninety-second reader
sees it, once as the closing block so a full read ends on it.

**The run-flow strip** encodes real pipeline data: Route, Draft, Challenge, Reissue, Governance,
Gate, each carrying its actual value. Chevrons are CSS borders, not glyphs. It is the one piece of
visual structure on the page and it earns its place by being data.

## Rules this system holds to

- **Severity is symbol plus word.** `■■■ blocking`, `■■ serious`, `■ minor`. Never color alone,
  never a colored dot. The glyphs carry `aria-hidden` since the word is the accessible label.
- **WCAG 2.2 AA.** Body contrast ≥ 4.5:1, 44px minimum targets, reflow at 320px with no horizontal
  scroll, visible focus (`2px solid var(--accent)`, 3px offset), semantic landmarks, one `h1`.
- **No border-radius.** Anywhere, except 2px on focus rings.
- **No shadows.** The page holds without them, which is the test.
- **No icons and no emoji.** If a glyph is needed, it is drawn as CSS or inline SVG.
- **Cards only when the card is the interaction.** There are none on this page.
- **Numbering only where order is real.** Findings are numbered because they are an ordered set.
  Nothing else is.
- **`prefers-reduced-motion` respected.** There is no motion to suppress, and that is intentional.

## Deliberate exception

The decision bar uses `border-left: 4px solid var(--accent)`. This resembles a known AI-slop
pattern (colored left-border on cards). Kept knowingly: it is a single semantic emphasis on the
one element that matters most, not a decorative rail repeated across a card grid. If it ever
appears on a second element, it has become decoration and should be removed.

## Pending review state (decided 2026-09-03)

Added when the goal became a page the consulting lead reviews to decide, not only a record of a
decision already made. Same page, same debate, same Team's Plan — two things change:

- **The decision bar reports "not yet decided," never a verdict.** `--faint` for the border and
  `--ink-2` for the verdict text — deliberately neither the accent green (that is reserved for
  an actual decision) nor the forced amber (that would misreport a state nobody has reached).
  The closing section replaces the record (who, when, the hash-check note) with the exact CLI
  commands that would act on what the reader just read, `--force`/`--note` included when
  governance actually requires them — the CTA must never understate what a flagged run needs.
- **A "Team on this engagement" section**, right after the section divider and before Routing:
  every dispatched role's title and one-line remit, each linking to that specialist's own
  section. Answers "who is on this" as its own question rather than leaving it implied by the
  nav, on a page a reader may now open before knowing the team at all.

Forced approval was already decided before this (amber `#8a5a12`, documented under Color above);
listing it as undecided here was a stale carry-over from the original plan and is corrected.

## Not yet decided

- Treatment for rejected and errored-run states. Pending and forced are now both decided (this
  file, and the "Pending review state" section above); rejected and errored remain unspecified.
- Whether the artifact disclosure should render markdown or stay preformatted. The plan settles
  escaping (`html.escape` on everything); it does not settle rendering.
