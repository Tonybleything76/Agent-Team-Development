# DESIGN.md

The visual system for HuminLoop Agents' rendered run page (`huminloop render`).

## The pivot (2026-09-03)

The system below replaced an earlier one, "Institutional Briefing" — established 2026-08-31,
reference at `.design-work/run-renderer-reference.html` — built on the premise that the rendered
page was **an audit record, not a dashboard**: sober, one accent color reserved for the human
decision, no cards, no border-radius, no shadows, dense Spectral-serif prose blocks.

Tony's reaction to the first real run rendered in that system was immediate and specific: *"I
don't know who they are. I don't know anything about them... I would never even show anybody
this."* That wasn't a taste disagreement to negotiate — the brief had changed. The goal became a
page to run live, show people, and use to actually review an engagement as its consulting lead,
and a quiet audit record is a different artifact from a dashboard someone wants to show off. The
premise itself was wrong for the job, not just its execution.

**What carried over:** the underlying content model (Team's Plan leading, per-advisor Critique
and Artifact sections, the decision/CTA at the close), WCAG 2.2 AA, `prefers-reduced-motion`,
severity as color **plus** a visible word (never color alone), and the light/dark token
structure's mechanics (bare `:root` = light, media query and `[data-theme]` override, `:not()`
guard). **What didn't:** the no-radius/no-cards/one-accent/serif-prose rules, and the assumption
that dark should ever be the *silent* default — it had been, via `prefers-color-scheme`, with no
way to override it short of changing the OS setting. That is now an explicit, in-page toggle,
defaulting to light regardless of OS preference.

## What this system is for

Still one page type: the rendered run. Now explicitly a **dashboard the consulting lead runs
and reviews**, before a decision as much as after one (see `huminloop/render.py`'s pending-state
support) — not a document optimized for a single careful read, but a page optimized for orienting
in five seconds, then drilling into whatever's relevant.

## Color — a validated palette, not picked by eye

Chosen and checked against the dataviz skill's palette validator (`scripts/validate_palette.js`),
not eyeballed. Values below are the categorical/status slots actually in use in `render.py`'s
`CSS` constant — that constant is the source of truth; this table documents it, not the reverse.

| Token | Light | Dark | Use |
|---|---|---|---|
| `--page` | `#f9f9f7` | `#0d0d0d` | Page background outside cards. |
| `--surface` | `#fcfcfb` | `#1a1a19` | Card/tile/details background. |
| `--surface-2` | `#f2f2ef` | `#212120` | Nested surface (quote blocks, chips). |
| `--ink` | `#0b0b0b` | `#ffffff` | Primary text. |
| `--ink-2` | `#52514e` | `#c3c2b7` | Secondary prose. |
| `--muted` | `#898781` | `#9a9890` | Labels, metadata. |
| `--rule` | `#e1e0d9` | `#2c2c2a` | Borders. |
| `--accent` | `#2a78d6` | `#5b9fed` | Team identity, links, the pending-review state. |
| `--good` | `#0ca30c` | `#39c239` | Resolved findings, approved gate. |
| `--warning` / `--warning-ink` | `#c98500` / `#8a5a12` | `#fab219` / `#fed07a` | Disagreements, forced approval. |
| `--critical` | `#c23333` | `#f0837f` | Escalations, blocking findings. |

**Status color never carries meaning alone.** Every severity badge and disagreement/escalation
marker pairs its color with a visible word (`Blocking`, `Serious`, `Minor`; the register's own
name). This rule survived the pivot unchanged.

Team-member avatars use a fixed eight-color categorical order (`_TEAM_COLORS` in `render.py`),
assigned by dispatch position within a run and never reassigned — identity, not rank.

**Theme structure.** Bare `:root` carries light. `@media (prefers-color-scheme: dark)` guarded
as `:root:not([data-theme="light"])` redefines tokens for OS-dark readers who haven't toggled.
`:root[data-theme="dark"]` redefines them again for an explicit toggle choice. A small inline
script stamps `data-theme="light"` on load unless `localStorage` says otherwise — **light is the
default regardless of OS setting**; a reader gets dark only by asking for it, via the toggle in
the header.

## Type

One face: Public Sans, from Google Fonts, with a real fallback stack
(`-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`). Spectral (the audit-record serif)
is gone — a dashboard scans in one voice, not two.

## Layout

Sticky index left (200px), content right, collapsing to a horizontal scroller under 880px.

Header order: product identity + theme toggle, orientation sentence, task, **stat tiles**
(advisors dispatched, findings challenged, disagreements, escalations, gate status — real
numbers from the run, severity colored), decision bar. Below the header: **Team on this
engagement** first (a card grid — colored initials avatar, title, remit, a "challenged ·
resolved" chip), then the Team's Plan, then routing and each advisor's collapsed Critique and
Artifact.

**Cards are back, deliberately.** The prior system banned them ("cards only when the card is the
interaction — there are none on this page"). On a dashboard, the team roster and the stat row
*are* the interaction: distinct, scannable units a reader compares at a glance. Border-radius
(8–14px) is used the same way — softness signaling "this is a scannable module," not decoration
for its own sake.

**Density is collapsed by default.** Both the Critique and the Artifact section for every
advisor are `<details>`, closed on load, showing only a one-line summary (challenge count,
resolved count). The prior system opened Critique unconditionally, which is exactly the "wall of
text" the goal called out. A reader now sees seven compact rows before choosing what to expand.

## Rules this system holds to

- **Severity is color plus a visible word**, never color alone (see Color above).
- **WCAG 2.2 AA.** Body contrast ≥ 4.5:1, 44px minimum targets, reflow at 320px with no
  horizontal scroll, visible focus (`2px solid var(--accent)`, 3px offset), semantic landmarks.
- **No shadows.** Cards separate by border and surface-color contrast, not elevation.
- **No icons and no emoji.** Team identity is a colored initials avatar (typographic), not a
  pictogram.
- **`prefers-reduced-motion` respected.**
- **Light is the default, unconditionally.** Dark is opt-in via the toggle, remembered in
  `localStorage`, never silently inherited from the OS.

## Not yet decided

- Treatment for rejected and errored-run states (unchanged from before the pivot — still
  genuinely undesigned; `render_run` still refuses both with `RenderError`).
- Whether the artifact disclosure should render markdown or stay preformatted. Escaping is
  settled (`html.escape` on everything); rendering is not.
- A true live view of a run in progress — this system covers the finished (or pending) report,
  not a running one. Watching agents work in real time would need a running process pushing
  updates, not a static file generated after the fact; that's a distinct, larger feature, not
  attempted here.
