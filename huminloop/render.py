"""Render a run's manifest and artifacts into the DESIGN.md HTML report.

Two pivots landed the same day (2026-09-03): "Institutional Briefing" (a quiet audit record) to
a dashboard (stat tiles, a card-grid roster, color), then the dashboard to a narrative — a page
read start to finish, not scanned, once it turned out a dashboard was still the wrong shape.
See DESIGN.md's "Two pivots, in order" for the full account, including the exact feedback that
drove each one. This module is the source of truth for the visual system — the old reference
file is historical, not authoritative.

Approved and pending runs are both supported. Pending is the review surface: the consulting
lead reads the same page — every advisor's account of their own reasoning, the pushback they
took and why they revised, where they disagreed, the plan — and acts from the exact CLI commands
the decision section prints, rather than reading a terminal `show` dump first. Rejected and
errored-run states remain visually undecided (see DESIGN.md "Not yet decided") and rendering one
would be inventing a design this project has not actually settled on.
"""

import html
import re
from pathlib import Path

from .gate import verify_artifacts
from .governance import flagged_roles, split_sections
from .orchestrator import SYNTHESIS_ROLE, parse_registers
from .roles import get_role

CSS = """
:root{
  --page:#ffffff;
  --surface:#f5f5f7;
  --surface-2:#eceef3;
  --ink:#1a1a2e;
  --ink-2:#3d3d5c;
  --muted:#5b6270;
  --rule:#e8e8f0;
  --rule-soft:#eef0f5;
  --accent:#7a78f5;
  --accent-2:#ec6496;
  --accent-ink:#4a47b8;
  --accent-wash:#edecfd;
  --good:#0ca30c;
  --good-wash:#e8f7e8;
  --warning:#c98500;
  --warning-ink:#8a5a12;
  --warning-wash:#fdf1da;
  --critical:#c23333;
  --critical-wash:#fbe9e8;
  --avatar-ink:#ffffff;
  --story-wash:#f6f3fb;
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --page:#14141f;
    --surface:#1e1e2f;
    --surface-2:#262638;
    --ink:#f2f1f7;
    --ink-2:#cfcee0;
    --muted:#a4a2c0;
    --rule:#34334a;
    --rule-soft:#2b2a3f;
    --accent:#9b99f7;
    --accent-2:#f5a0c4;
    --accent-ink:#b4b2ff;
    --accent-wash:#2a2850;
    --good:#39c239;
    --good-wash:#173317;
    --warning:#fab219;
    --warning-ink:#fed07a;
    --warning-wash:#332708;
    --critical:#f0837f;
    --critical-wash:#341918;
    --story-wash:#241f34;
  }
}
:root[data-theme="dark"]{
  --page:#14141f;
  --surface:#1e1e2f;
  --surface-2:#262638;
  --ink:#f2f1f7;
  --ink-2:#cfcee0;
  --muted:#a4a2c0;
  --rule:#34334a;
  --rule-soft:#2b2a3f;
  --accent:#9b99f7;
  --accent-2:#f5a0c4;
  --accent-ink:#b4b2ff;
  --accent-wash:#2a2850;
  --good:#39c239;
  --good-wash:#173317;
  --warning:#fab219;
  --warning-ink:#fed07a;
  --warning-wash:#332708;
  --critical:#f0837f;
  --critical-wash:#341918;
  --story-wash:#241f34;
}
*{box-sizing:border-box}
body{
  margin:0;
  background:var(--page);
  color:var(--ink-2);
  font-family:"Inter",-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
  font-size:17px;
  line-height:1.65;
  -webkit-font-smoothing:antialiased;
}
a{color:var(--accent-ink);text-decoration:none}
a:hover{color:var(--accent);text-decoration:underline}
:focus-visible{outline:2px solid var(--accent);outline-offset:3px;border-radius:2px}
code{
  font-family:ui-monospace,"SF Mono",Menlo,monospace;
  background:var(--surface-2);padding:2px 6px;font-size:.85em;border-radius:4px;
}
.wrap{max-width:760px;margin:0 auto;padding:clamp(24px,4vw,56px) clamp(20px,4vw,32px) 140px}

/* ---- header ---- */
.topbar{display:flex;justify-content:space-between;align-items:center;gap:16px;flex-wrap:wrap}
.brandmark{display:flex;align-items:center;gap:10px}
.loop-mark{
  width:22px;height:22px;border-radius:50%;flex-shrink:0;
  background:conic-gradient(
    from 200deg,#5ea0e8,#7a78f5,#9752fa,#c849d8,#ec6496,#f47c71,#f9c040,#5ea0e8
  );
}
.brand-word{
  font-family:"DM Sans",sans-serif;font-weight:700;font-size:14px;
  color:var(--ink);letter-spacing:-.01em;
}
.rid{
  font-size:11px;letter-spacing:.14em;text-transform:uppercase;
  color:var(--muted);font-weight:700;font-family:"DM Sans",sans-serif;
  font-variant-numeric:tabular-nums;
  display:flex;flex-wrap:wrap;gap:6px 14px;margin-top:16px;
}
.rid span::after{content:" \\00b7";color:var(--rule)}
.rid span:last-child::after{content:""}
.theme-toggle{
  appearance:none;border:1px solid var(--rule);background:var(--surface);color:var(--ink-2);
  font-family:"DM Sans",sans-serif;font-size:13px;font-weight:600;padding:8px 14px;
  border-radius:8px;cursor:pointer;min-height:44px;flex-shrink:0;
}
.theme-toggle:hover{border-color:var(--accent);color:var(--ink)}
.orient{
  margin:22px 0 0;max-width:68ch;
  font-size:17px;line-height:1.6;color:var(--ink-2);
}
h1.task{
  font-family:"DM Sans",sans-serif;
  font-weight:700;
  font-size:clamp(24px,4vw,34px);
  line-height:1.2;
  letter-spacing:-.01em;
  margin:24px 0 6px;
  color:var(--ink);
  text-wrap:balance;
}
.task-context{
  margin:0 0 4px;max-width:68ch;
  font-size:15px;line-height:1.6;color:var(--ink-2);
}
.summary-line{
  margin:22px 0 0;padding:16px 20px;background:var(--surface-2);border-radius:10px;
  font-size:16px;line-height:1.6;color:var(--ink-2);max-width:68ch;
}
.summary-line b{font-family:"DM Sans",sans-serif;color:var(--ink);font-variant-numeric:tabular-nums}
.summary-line b.warn{color:var(--warning-ink)}
.summary-line b.crit{color:var(--critical)}
.chip{
  display:inline-flex;align-items:center;gap:6px;padding:5px 12px;border-radius:999px;
  font-family:"DM Sans",sans-serif;font-size:13px;font-weight:700;letter-spacing:.01em;
}
.chip-pending{background:var(--accent-wash);color:var(--accent-ink)}
.chip-good{background:var(--good-wash);color:var(--good)}
.chip-warning{background:var(--warning-wash);color:var(--warning-ink)}

/* ---- table of contents ---- */
#team{margin-top:36px}
#team h2{margin-bottom:2px}
.toc-list{list-style:none;margin:14px 0 0;padding:0;display:flex;flex-direction:column;gap:2px}
.toc-list li{border-top:1px solid var(--rule-soft)}
.toc-list li:first-child{border-top:none}
.toc-list a{
  display:flex;align-items:center;gap:12px;padding:11px 4px;color:inherit;text-decoration:none;
}
.toc-list a:hover{color:var(--accent)}
.toc-list a:hover .toc-name{color:var(--accent)}
.avatar{
  flex-shrink:0;width:32px;height:32px;border-radius:50%;
  display:flex;align-items:center;justify-content:center;
  font-size:12px;font-weight:700;color:var(--avatar-ink);
}
.toc-name{font-family:"DM Sans",sans-serif;font-weight:700;font-size:16px;color:var(--ink)}
.toc-remit{font-size:13px;color:var(--muted);margin-left:auto;text-align:right;max-width:38ch}
@media (max-width:640px){.toc-remit{display:none}}

/* ---- generic section rhythm ---- */
section{margin:0 0 12px}
.act{margin:56px 0 0;padding-top:32px;border-top:1px solid var(--rule)}
.act:first-of-type{margin-top:44px}
.act-label{
  font-family:"DM Sans",sans-serif;
  font-size:12px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--accent-ink);
  margin:0 0 6px;
}
h2{
  font-family:"DM Sans",sans-serif;font-weight:700;
  font-size:24px;letter-spacing:-.005em;margin:0 0 8px;color:var(--ink);
}
.sub{font-size:15px;color:var(--muted);margin:0 0 20px;max-width:68ch;line-height:1.55}

/* ---- advisor story ---- */
details.story{margin:0 0 8px}
details.story > summary{
  list-style:none;cursor:pointer;
  display:flex;align-items:center;gap:12px;
  padding:14px 4px;border-top:1px solid var(--rule);
}
details.story:first-of-type > summary{border-top:none}
details.story > summary::-webkit-details-marker{display:none}
details.story > summary::after{
  content:"\\25be";margin-left:auto;color:var(--muted);font-size:13px;flex-shrink:0;
}
details.story[open] > summary::after{content:"\\25b4"}
.story-name{font-family:"DM Sans",sans-serif;font-weight:700;font-size:19px;color:var(--ink)}
.story-remit{font-size:13px;color:var(--muted)}
.story-body{padding:4px 4px 28px;max-width:68ch}
.story-body h4{
  font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);
  margin:22px 0 8px;font-weight:700;
}
.story-body h4:first-child{margin-top:2px}
.story-body p{margin:0 0 12px;color:var(--ink-2);line-height:1.65}
.story-body ul,.story-body ol{margin:0 0 12px;padding-left:1.3em;color:var(--ink-2)}
.story-body li{margin:0 0 6px}
.voice{padding:16px 18px;border-radius:10px;margin:0 0 14px}
.voice > .lbl{
  font-size:11px;letter-spacing:.08em;text-transform:uppercase;font-weight:700;margin-bottom:8px;
  display:block;
}
.voice p{margin:0;line-height:1.6}
.voice.position{background:var(--surface-2)}
.voice.position .lbl{color:var(--muted)}
.voice.pushback{background:var(--story-wash);border-left:3px solid var(--warning)}
.voice.pushback .lbl{color:var(--warning-ink)}
.voice.pushback .sev{
  display:inline-block;font-size:10px;font-weight:700;text-transform:uppercase;
  letter-spacing:.05em;padding:2px 8px;border-radius:999px;margin-right:8px;
  background:var(--warning-wash);color:var(--warning-ink);
}
.voice.pushback .sev.crit{background:var(--critical-wash);color:var(--critical)}
.voice.pushback .sev.info{background:var(--surface-2);color:var(--ink-2)}
.voice.revision{background:var(--good-wash);border-left:3px solid var(--good)}
.voice.revision .lbl{color:var(--good)}
.exchange{margin:0 0 22px}
.exchange:last-child{margin-bottom:0}
.cite-list{font-size:13px;color:var(--muted);margin:14px 0 0}
.cite-list a{color:var(--accent-ink)}

/* ---- plan / registers ---- */
.quote{
  background:var(--surface-2);padding:18px 20px;margin:0 0 16px;
  max-width:68ch;border-radius:10px;
}
.quote.hero{
  padding-left:22px;border-radius:0 10px 10px 0;
  border-left:3px solid transparent;
  border-image:linear-gradient(var(--accent),var(--accent-2)) 1;
}
.quote .lbl{
  font-family:"DM Sans",sans-serif;
  font-size:11px;letter-spacing:.1em;text-transform:uppercase;
  color:var(--muted);font-weight:700;margin-bottom:8px;
}
.quote p{margin:0;font-size:16px;line-height:1.6;color:var(--ink-2)}
.register{margin:0 0 28px}
.register:last-child{margin-bottom:8px}
.register-head{display:flex;align-items:baseline;gap:10px;margin:0 0 4px}
.register-head h3{
  font-family:"DM Sans",sans-serif;font-size:13px;font-weight:700;
  letter-spacing:.08em;text-transform:uppercase;color:var(--ink-2);margin:0;
}
.register-count{
  font-size:12px;font-weight:700;color:var(--ink-2);background:var(--surface-2);
  border-radius:999px;padding:2px 9px;
}
.register-disagreements .register-count{background:var(--warning-wash);color:var(--warning-ink)}
.register-escalations .register-count{background:var(--critical-wash);color:var(--critical)}
.register-note{font-size:13px;color:var(--muted);margin:2px 0 10px;max-width:65ch}
.reg-item{
  padding:12px 0;border-top:1px solid var(--rule-soft);display:flex;
  gap:14px;align-items:flex-start;
}
.reg-item .n{
  flex-shrink:0;display:flex;align-items:center;justify-content:center;
  min-width:24px;height:24px;border-radius:50%;
  font-weight:700;font-size:12px;background:var(--surface-2);color:var(--ink-2);
}
.register-disagreements .reg-item .n{background:var(--warning-wash);color:var(--warning-ink)}
.register-escalations .reg-item .n{background:var(--critical-wash);color:var(--critical)}
.reg-item p{margin:0;max-width:65ch;color:var(--ink);font-size:16px;line-height:1.55}
.reg-item .owner-note{font-size:13px;color:var(--muted);margin-top:4px}

/* ---- milestones ---- */
.milestones{list-style:none;margin:8px 0 0;padding:0;counter-reset:milestone}
.milestone{
  display:flex;gap:16px;padding:16px 0;border-top:1px solid var(--rule-soft);align-items:flex-start;
}
.milestone:first-child{border-top:none}
.milestone .num{
  flex-shrink:0;width:28px;height:28px;border-radius:50%;background:var(--accent-wash);
  color:var(--accent-ink);font-family:"DM Sans",sans-serif;font-weight:700;font-size:13px;
  display:flex;align-items:center;justify-content:center;
}
.milestone p{margin:0;color:var(--ink);font-size:16px;line-height:1.55;max-width:62ch}
.risks-box{
  background:var(--critical-wash);padding:18px 20px;border-radius:10px;
  margin:8px 0 0;max-width:68ch;
}
.risks-box p{margin:0;color:var(--ink-2);font-size:15px;line-height:1.6}

/* ---- errored / absent ---- */
.absent{
  padding:18px 20px;background:var(--warning-wash);max-width:68ch;
  font-size:15px;color:var(--ink);border-radius:10px;
}

/* ---- decision ---- */
.decision{
  border:1px solid var(--rule);border-radius:14px;padding:26px 28px;background:var(--surface);
  margin-top:44px;
}
.decision.forced{border-color:var(--warning-ink);background:var(--warning-wash)}
.decision.pending{border-color:var(--accent);background:var(--accent-wash)}
.decision .verdict{font-family:"DM Sans",sans-serif;font-size:22px;font-weight:700;color:var(--ink)}
.decision.forced .verdict{color:var(--warning-ink)}
.decision.pending .verdict{color:var(--accent-ink)}
.decision .cta{font-size:15px;margin:12px 0 0;max-width:64ch;color:var(--ink-2)}
.decision .cmd{
  margin-top:14px;display:flex;flex-direction:column;gap:8px;
  font-family:ui-monospace,"SF Mono",Menlo,monospace;font-size:13px;
}
.decision .cmd code{
  background:var(--surface);padding:10px 14px;display:block;max-width:100%;
  overflow-x:auto;white-space:pre;border-radius:8px;border:1px solid var(--rule);
}
.decision .flag-list{margin-top:14px;font-size:13px;color:var(--warning-ink);font-weight:700}
.decision .who{
  font-family:"DM Sans",sans-serif;font-size:26px;font-weight:700;
  margin-top:8px;color:var(--ink);
}
.decision .when{font-size:13px;color:var(--muted);margin-top:4px;font-variant-numeric:tabular-nums}
.decision .note{font-size:15px;margin:14px 0 0;max-width:60ch;color:var(--ink-2)}
.decision .force-note{margin-top:12px;font-size:13px;color:var(--warning-ink);font-weight:700}
@media (max-width:640px){
  .wrap{padding-left:16px;padding-right:16px}
}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
"""

_HTTPS_RE = re.compile(r"https://\S+")
_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")
_NUMBERED_LINE_RE = re.compile(r"^[ \t]*\d+[.)][ \t]*(.+)$")


class RenderError(Exception):
    pass


def esc(text: str | None) -> str:
    return html.escape(text or "", quote=True)


_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
_ITALIC_RE = re.compile(r"(?<!\*)\*([^*]+?)\*(?!\*)")


def mdlite(text: str | None) -> str:
    """Escape everything, then interpret the one piece of markup the model actually writes:
    **bold** and *italic*. Escaping first means a literal '<' in the model's own text can never
    become a tag — the <b>/<em> this function inserts afterward are ours, not the model's, so
    this stays exactly as safe as plain esc() while no longer leaving raw asterisks on the page.
    """
    escaped = esc(text)
    escaped = _BOLD_RE.sub(r"<b>\1</b>", escaped)
    return _ITALIC_RE.sub(r"<em>\1</em>", escaped)


def _linkify(escaped_line: str) -> str:
    """Wrap bare https URLs in an already-escaped line. Escape first, link second: the href
    itself is built from already-safe text, so no further escaping is needed inside it."""
    return _HTTPS_RE.sub(lambda m: f'<a href="{m.group(0)}">{m.group(0)}</a>', escaped_line)


def _slug(role: str) -> str:
    return role.replace("_", "-")


# A headline this long stops being "pithy" no matter which sentence supplies it — DESIGN.md's
# 22ch display-type column reads as an intentional magazine-style headline only when the text
# is actually short; forcing a 30-word sentence into it just wraps ten lines of giant serif type,
# the same "scrunched" failure a short headline never has. Past this length there is no genuinely
# pithy candidate in the task, so the caller falls back to a plain quote block instead of a
# headline — never inventing a shorter paraphrase to force the display treatment to fit.
PITHY_MAX_CHARS = 90


def split_headline(task: str) -> tuple[str, str]:
    """A pithy h1 plus supporting detail, built from the task's own sentences — never a
    paraphrase. Prefers a trailing question (usually the actual ask); falls back to the leading
    sentence when the task doesn't end that way, or to the whole task when it is one sentence.
    Returns an empty headline when no candidate is actually short — see PITHY_MAX_CHARS.
    """
    task = (task or "").strip()
    sentences = [s.strip() for s in _SENTENCE_RE.split(task) if s.strip()]
    if len(sentences) > 1 and sentences[-1].endswith("?"):
        headline, context = sentences[-1], " ".join(sentences[:-1])
    elif len(sentences) > 1:
        headline, context = sentences[0], " ".join(sentences[1:])
    else:
        headline, context = task, ""
    if len(headline) > PITHY_MAX_CHARS:
        return "", task
    return headline, context


def _split_decision(line: str) -> tuple[str, str | None]:
    if " -> " in line:
        text, owner = line.rsplit(" -> ", 1)
        return text.strip(), owner.strip()
    return line, None


def _render_citations(body: str) -> str:
    items = [ln.strip().lstrip("-").strip() for ln in body.splitlines() if ln.strip()]
    if not items:
        return ""
    lis = "\n".join(f"<li>{_linkify(mdlite(item))}</li>" for item in items)
    return f"<ul>{lis}</ul>"


def _render_next_steps(body: str) -> str:
    lines = [ln.strip() for ln in body.splitlines() if ln.strip()]
    numbered = [_NUMBERED_LINE_RE.match(ln) for ln in lines]
    if lines and all(numbered):
        lis = "\n".join(f"<li>{mdlite(m.group(1))}</li>" for m in numbered)
        return f"<ol>{lis}</ol>"
    return "".join(f"<p>{mdlite(p)}</p>" for p in body.split("\n\n") if p.strip())


def _render_prose(body: str) -> str:
    return "".join(f"<p>{mdlite(p.strip())}</p>" for p in body.split("\n\n") if p.strip())


def _parse_milestones(body: str) -> list[str]:
    """The Lead's Next Steps as discrete milestones, not a paragraph blob — same numbered-line
    detection as _render_next_steps, but returning plain strings so the caller can give each
    one its own visually distinct block."""
    lines = [ln.strip() for ln in body.splitlines() if ln.strip()]
    numbered = [_NUMBERED_LINE_RE.match(ln) for ln in lines]
    if lines and all(numbered):
        return [m.group(1) for m in numbered]
    return [p.strip() for p in body.split("\n\n") if p.strip()]


def _plan_counts(lead_text: str | None) -> dict:
    """Decisions/disagreements/escalations counts, computed once and reused by the stat tiles
    and by the Team's Plan section itself — the tiles must report the real numbers from this
    run, not a second, potentially-drifting count."""
    if not lead_text:
        return {"decisions": 0, "disagreements": 0, "escalations": 0}
    body = split_sections(lead_text).get("body", "")
    regs = parse_registers(body)
    return {
        "decisions": len(regs.get("decisions") or []),
        "disagreements": len(regs.get("disagreements") or []),
        "escalations": len(regs.get("escalations") or []),
    }


def _summary_line(manifest: dict, plan_counts: dict) -> str:
    """One orienting sentence, not a grid of tiles — this page is a story to read, not a
    dashboard to scan. The numbers are still real and still colored by severity; they just
    live in a sentence instead of a card."""
    plan = manifest.get("plan") or {}
    artifacts = manifest.get("artifacts") or []
    n_specialists = len(plan.get("roles") or [])
    n_findings = sum(
        len((a.get("critique") or {}).get("points") or [])
        for a in artifacts
        if a.get("role") != SYNTHESIS_ROLE
    )
    status = manifest.get("status")
    decision = manifest.get("decision") or {}
    forced = bool(decision.get("forced"))
    if status == "pending":
        gate_html = '<span class="chip chip-pending">awaiting your decision</span>'
    elif forced:
        gate_html = '<span class="chip chip-warning">approved &mdash; forced</span>'
    else:
        gate_html = '<span class="chip chip-good">approved</span>'

    n_disagreements = plan_counts["disagreements"]
    n_escalations = plan_counts["escalations"]
    disagree_cls = " warn" if n_disagreements else ""
    escalate_cls = " crit" if n_escalations else ""
    findings_word = "finding" if n_findings == 1 else "findings"
    specialist_word = "specialist" if n_specialists == 1 else "specialists"
    return (
        '<p class="summary-line">'
        f"We dispatched <b>{n_specialists}</b> {specialist_word} and challenged each "
        f"other <b>{n_findings}</b> {findings_word} deep. We reached "
        f'<b class="{disagree_cls.strip()}">'
        f"{n_disagreements}</b> open disagreement{'s' if n_disagreements != 1 else ''} and "
        f'<b class="{escalate_cls.strip()}">{n_escalations}</b> question'
        f"{'s' if n_escalations != 1 else ''} only you can answer. This run is {gate_html}.</p>"
    )


def _pending_decision_bar(manifest: dict) -> str:
    """The review surface for a run nobody has decided yet.

    Not a smaller version of the decided bar — a different purpose. It never claims a verdict
    (there is none), and instead of a record it prints the exact commands that would act on
    what the reader just read, including the --force and --note a flagged role actually requires
    so the CTA never lies about how easy the decision in front of them is. Appears once, at the
    close — the summary line up top already carries a compact "awaiting your decision" chip, so
    the full record isn't duplicated before the story has even been told.
    """
    run_id = manifest.get("run_id", "")
    flagged = flagged_roles(manifest.get("artifacts") or [])
    if flagged:
        approve_cmd = (
            f'huminloop approve {run_id} --by "Your Name" --force --note "..."'
        )
        flag_html = (
            f'<p class="flag-list">{len(flagged)} role(s) carried findings that require '
            f"<code>--force</code> and a <code>--note</code> to approve: "
            f'{esc(", ".join(flagged))}.</p>'
        )
    else:
        approve_cmd = f'huminloop approve {run_id} --by "Your Name"'
        flag_html = ""
    reject_cmd = f'huminloop reject {run_id} --by "Your Name" --reason "..."'
    return (
        '<section id="decision" class="decision pending">\n'
        "<h2>Your decision</h2>\n"
        '<p class="sub">Nothing here goes anywhere until you read it and say yes. The debate '
        "is above &mdash; every one of our drafts, what got challenged, and the plan we "
        "built, at the top.</p>\n"
        '<div class="verdict">NOT YET DECIDED</div>\n'
        '<p class="cta">Act from here once you have read it:</p>\n'
        '<div class="cmd">\n'
        f"<code>{esc(approve_cmd)}</code>\n"
        f"<code>{esc(reject_cmd)}</code>\n"
        "</div>\n"
        f"{flag_html}\n"
        "</section>"
    )


def _decision_bar(manifest: dict) -> str:
    """The record of what was decided, once — at the close, as the ending of the story rather
    than a verdict spoiled at the top before any of it has been read."""
    if manifest.get("status") == "pending":
        return _pending_decision_bar(manifest)
    decision = manifest.get("decision") or {}
    state = decision.get("state", "")
    forced = bool(decision.get("forced"))
    verdict = state.upper()
    if forced:
        verdict += " &mdash; FORCED"
    note = (
        f'<p class="note">&ldquo;{esc(decision.get("note", ""))}&rdquo;</p>'
        if decision.get("note")
        else ""
    )
    cls = "decision forced" if forced else "decision"
    force_note = ""
    if forced:
        flagged = decision.get("flagged_roles") or []
        force_note = (
            f'<p class="force-note">Forced: {len(flagged)} role(s) carried findings a '
            "human had to override in writing before this could be approved.</p>"
        )
    artifacts = manifest.get("artifacts") or []
    clean = sum(1 for a in artifacts if a.get("sha256"))
    return (
        f'<section id="decision" class="{cls}">\n'
        "<h2>Human decision</h2>\n"
        '<p class="sub">Nothing here went anywhere until you read it and said yes. '
        "Before recording that, we re-read every document to check nothing had "
        "changed since you looked.</p>\n"
        f'<div class="verdict">{verdict}</div>\n'
        f'<div class="who">{esc(decision.get("by", ""))}</div>\n'
        f'<div class="when">{esc(decision.get("at", ""))}</div>\n'
        f"{note}\n{force_note}\n"
        f'<p class="hash">Artifacts verified at decision time &middot; {clean} artifact(s), '
        f'all sha256-checked &middot; forced: {str(forced).lower()} &middot; '
        f'flagged roles: {esc(", ".join(decision.get("flagged_roles") or []) or "none")}</p>\n'
        "</section>"
    )


# Fixed categorical order (never cycled/reassigned within a run) — a validated palette, not
# picked by eye. See the dataviz skill's reference palette: worst adjacent CVD Delta E 9.1,
# worst adjacent normal-vision Delta E 19.6, both clear of the safety floor.
_TEAM_COLORS = (
    "#2a78d6",  # blue
    "#eb6834",  # orange
    "#1baf7a",  # aqua
    "#c98500",  # yellow, darkened for AA text-free contrast as a fill
    "#c9578a",  # magenta, darkened from the reference step for the same reason
    "#008300",  # green
    "#4a3aa7",  # violet
    "#c23333",  # red, matched to --critical so it doesn't compete with severity color
)
_STOPWORDS = {"and", "the", "of", "for"}


def _initials(title: str) -> str:
    words = [w for w in re.split(r"[\s/&]+", title) if w and w.lower() not in _STOPWORDS]
    letters = "".join(w[0] for w in words[:2]).upper()
    return letters or title[:2].upper()


def _toc(artifacts: list[dict]) -> str:
    """A table of contents, not a persistent sidebar to scan against every section: "here is
    who was in the room," stated once, near the top, then the page moves on to the story of
    what they actually said. Each row still links to that specialist's full account below."""
    items = []
    for i, a in enumerate(artifacts):
        role = a["role"]
        r = get_role(role)
        href = "#plan" if role == SYNTHESIS_ROLE else f"#a-{_slug(role)}"
        color = _TEAM_COLORS[i % len(_TEAM_COLORS)]
        items.append(
            f'<li><a href="{href}">'
            f'<span class="avatar" style="background:{color}">{esc(_initials(r.title))}</span>'
            f'<span class="toc-name">{esc(r.title)}</span>'
            f'<span class="toc-remit">{esc(r.instruction)}</span>'
            "</a></li>"
        )
    return (
        '<section id="team"><h2>Who we put on this</h2>'
        '<p class="sub">Every seat we dispatched for this task. What follows is the '
        "story of what each of us said, in the order we said it.</p>"
        f'<ul class="toc-list">{"".join(items)}</ul></section>'
    )


_SEV_STATUS = {"blocking": "crit", "serious": "warn", "minor": "info"}


def _critique_summary_line(critique: dict) -> str:
    points = critique.get("points") or []
    accepted = sum(1 for p in points if p.get("disposition") == "accepted")
    summary = f'{len(points)} challenge{"s" if len(points) != 1 else ""}'
    if points:
        summary += f" &middot; {accepted} resolved"
    return summary


def _critique_exchanges_html(critique: dict) -> str:
    """The pushback-and-response half of a story: steelman, pre-mortem, then each finding
    paired immediately with the revision it produced (or the response given if it wasn't
    accepted). Shared between a specialist's own account and the Engagement Lead's — the plan
    gets challenged too (orchestrator._do_synthesis), and it deserves the same treatment."""
    parts = []
    if critique.get("steelman"):
        parts.append(
            '<div class="voice pushback"><div class="lbl">The strongest case for it</div>'
            f"<p>{mdlite(critique['steelman'])}</p></div>"
        )
    if critique.get("premortem"):
        parts.append(
            '<div class="voice pushback"><div class="lbl">How this could go wrong</div>'
            f"<p>{mdlite(critique['premortem'])}</p></div>"
        )
    for i, p in enumerate(critique.get("points") or [], 1):
        sev = (p.get("severity") or "minor").lower()
        status = _SEV_STATUS.get(sev, "info")
        dim = esc(p.get("dimension", ""))
        parts.append('<div class="exchange">')
        parts.append(
            f'<div class="voice pushback"><div class="lbl">Pushback {i}'
            f'{" &middot; " + dim if dim else ""}</div>'
            f'<p><span class="sev {status}">{esc(sev.title())}</span>'
            f"{mdlite(p.get('claim', ''))}</p></div>"
        )
        if p.get("response"):
            resolved = p.get("disposition") == "accepted"
            label = "Why they revised it" if resolved else "Their response"
            parts.append(
                f'<div class="voice revision"><div class="lbl">{label}</div>'
                f"<p>{mdlite(p['response'])}</p></div>"
            )
        parts.append("</div>")  # .exchange
    return "\n".join(parts)


def _advisor_story(role: str, artifact: dict, text: str) -> str:
    """One advisor's whole account, in the order it actually happened: what they were asked and
    concluded, what they cited, the pushback the critic raised and why, and — paired right next
    to each piece of pushback — why they revised (or didn't) in response. This replaces what
    used to be two separate collapsed sections (Critique, then Artifact): a story reads as one
    continuous account, not as two disclosures a reader has to open separately and reassemble
    themselves. Open by default — this page is read start to finish, not scanned; the <details>
    wrapper still lets a reader collapse an advisor they've already read.
    """
    r = get_role(role)
    title = esc(r.title)
    sections = split_sections(text)
    critique = artifact.get("critique") or {}
    points = critique.get("points") or []

    remit_extra = ""
    if points:
        remit_extra = f" &mdash; {_critique_summary_line(critique)}"

    parts = [
        f'<details class="story" id="a-{_slug(role)}" open>',
        "<summary>"
        f'<span class="story-name">{title}</span>'
        f'<span class="story-remit">{esc(r.instruction)}{remit_extra}</span>'
        "</summary>",
        '<div class="story-body">',
    ]

    position = "\n\n".join(
        s for s in (sections.get("objective", ""), sections.get("body", "")) if s
    )
    position_html = "".join(
        f"<p>{mdlite(p.strip())}</p>" for p in position.split("\n\n") if p.strip()
    )
    if position_html:
        parts.append(
            '<div class="voice position"><div class="lbl">Their position</div>'
            f"{position_html}</div>"
        )
    citations = sections.get("citations", "")
    cite_items = [ln.strip().lstrip("-").strip() for ln in citations.splitlines() if ln.strip()]
    if cite_items:
        linked = ", ".join(_linkify(mdlite(item)) for item in cite_items)
        parts.append(f'<p class="cite-list"><b>Citing:</b> {linked}</p>')

    parts.append(_critique_exchanges_html(critique))

    risks = sections.get("risks", "")
    if risks:
        parts.append("<h4>What could go wrong</h4>")
        parts.append(_render_prose(risks))
    next_steps = sections.get("next steps", "")
    if next_steps:
        parts.append("<h4>What happens next</h4>")
        parts.append(_render_next_steps(next_steps))

    verdict = ((artifact.get("review") or {}).get("verdict") or "").lower()
    issues = (artifact.get("review") or {}).get("issues") or []
    gov = "passed" if not issues else f"{len(issues)} issue(s)"
    parts.append(
        f'<p class="sub">Automated checks: <b>{esc(gov)}</b>'
        f'{" (verdict: " + esc(verdict) + ")" if verdict else ""}.</p>'
    )
    parts.append("</div></details>")
    return "\n".join(parts)


def _absent_section(role: str, artifact: dict) -> str:
    title = esc(get_role(role).title)
    return (
        f'<div id="a-{_slug(role)}">\n'
        f'<h2>{title} <span class="kind">Status</span></h2>\n'
        f'<div class="absent">This seat produced nothing. {esc(artifact.get("error", ""))}</div>\n'
        "</div>"
    )


def _register_group(name: str, entries: list[str], *, item_class: str = "", note: str = "") -> str:
    """`note` is a hardcoded explainer string this module wrote, not model output — rendered
    as-is (it already carries its own entities), never passed through esc()."""
    count_label = f"{len(entries)}" if entries else "None"
    items = []
    for i, entry in enumerate(entries, 1):
        cls = f"reg-item {item_class}".strip()
        if name == "Decisions":
            # A bold "Owner: X" chip read as a confident assignment the model never actually
            # made — it's a role name the Lead guessed at, not someone who signed up for this.
            # Say so plainly instead of dressing a guess as a decision.
            text, owner = _split_decision(entry)
            owner_html = (
                f'<p class="owner-note">A likely owner, not a confirmed one: {esc(owner)}</p>'
                if owner
                else ""
            )
            items.append(
                f'<div class="{cls}"><span class="n">{i}</span>'
                f"<div><p>{mdlite(text)}</p>{owner_html}</div></div>"
            )
        else:
            items.append(
                f'<div class="{cls}"><span class="n">{i}</span><p>{mdlite(entry)}</p></div>'
            )
    note_html = f'<p class="register-note">{note}</p>' if note else ""
    # register-{name} lets the CSS color Disagreements amber and Escalations red without any
    # Python touching color decisions — severity is a display concern, not a content one.
    reg_cls = f"register register-{name.lower()}"
    return (
        f'<div class="{reg_cls}"><div class="register-head">'
        f"<h3>{esc(name)}</h3>"
        f'<span class="register-count">{count_label}</span></div>'
        f'{note_html}{"".join(items)}</div>'
    )


_RECOMMENDATION_END_RE = re.compile(
    r"^\s*#{1,6}\s*(?:Decisions|Disagreements|Escalations)\s*$",
    re.IGNORECASE | re.MULTILINE,
)


def _synthesis_section(artifact: dict, text: str) -> str:
    sections = split_sections(text)
    body = sections.get("body", "")
    regs = parse_registers(body)
    recommendation = _RECOMMENDATION_END_RE.split(body, maxsplit=1)[0]
    recommendation = re.sub(
        r"^\s*#{1,6}\s*Recommendation\s*$", "", recommendation, flags=re.M
    ).strip()

    parts = [
        '<section id="plan">',
        "<h2>Our Plan</h2>",
        '<p class="sub">Our Engagement Lead reads every one of our drafts in full and reports '
        "back: what we recommend, what we decided, where we pushed back on each other before "
        "settling, and what only you can answer. This is the one deliverable you act on "
        "&mdash; everything after this section is how we got here.</p>",
    ]
    if recommendation:
        parts.append(
            '<div class="quote hero"><div class="lbl">Recommendation</div>'
            f"<p>{mdlite(recommendation)}</p></div>"
        )
    parts.append(_register_group("Decisions", regs.get("decisions") or []))
    parts.append(
        _register_group(
            "Disagreements",
            regs.get("disagreements") or [],
            item_class="disagreement",
            note="Where we reached different conclusions and our Lead had to weigh them.",
        )
    )
    parts.append(
        _register_group(
            "Escalations",
            regs.get("escalations") or [],
            item_class="escalation",
            note=(
                "Questions none of us can answer for you &mdash; each one is why this "
                "run needed your sign-off."
            ),
        )
    )
    next_steps = sections.get("next steps", "")
    if next_steps:
        milestones = _parse_milestones(next_steps)
        items = "".join(
            f'<li class="milestone"><span class="num">{i}</span><p>{mdlite(m)}</p></li>'
            for i, m in enumerate(milestones, 1)
        )
        parts.append(
            '<div class="register"><div class="register-head">'
            "<h3>Milestones</h3>"
            f'<span class="register-count">{len(milestones)}</span></div>'
            '<p class="register-note">What has to happen, broken into steps you can track — '
            "not a paragraph to reread, a checklist to build from.</p>"
            f'<ol class="milestones">{items}</ol></div>'
        )
    risks = sections.get("risks", "")
    if risks:
        parts.append(
            '<div class="register"><div class="register-head"><h3>What Could Go Wrong</h3></div>'
            f'<div class="risks-box"><p>{mdlite(risks)}</p></div></div>'
        )
    lead_critique = artifact.get("critique")
    if lead_critique:
        # The plan gets challenged too — orchestrator._do_synthesis runs the same critique
        # loop on the Engagement Lead's synthesis as every specialist gets. The old renderer
        # never surfaced this at all; it's real debate, not a lesser or decorative addition.
        summary = _critique_summary_line(lead_critique)
        parts.append(
            '<details class="story" open>\n'
            "<summary>"
            '<span class="story-name">The plan itself was challenged</span>'
            f'<span class="story-remit">{summary}</span>'
            "</summary>\n"
            f'<div class="story-body">{_critique_exchanges_html(lead_critique)}</div>\n'
            "</details>"
        )
    parts.append("</section>")
    return "\n".join(parts)


def render_run(manifest: dict, run_dir: Path) -> str:
    """Render one run to a self-contained HTML page matching DESIGN.md.

    Approved and pending runs both render. Pending is not a lesser case: it is the page a
    consulting lead reviews *before* deciding, so it carries the same debate and the same Team's
    Plan, with the decision section replaced by a call to act rather than a record of one.
    """
    status = manifest.get("status")
    if status not in ("approved", "pending"):
        raise RenderError(
            f"run '{manifest.get('run_id')}' is {status!r}; only approved or pending runs can "
            "be rendered"
        )
    # Same integrity check either side of the decision: verify_artifacts re-derives each
    # artifact's review from the bytes on disk, so a pending render can't show a plan whose
    # governance verdict no longer matches what's actually there any more than an approved one.
    verify_artifacts(run_dir, manifest)

    artifacts = manifest.get("artifacts") or []
    texts = {
        a["role"]: (run_dir / a["file"]).read_text(encoding="utf-8")
        for a in artifacts
        if not a.get("error") and a.get("file")
    }
    headline, context = split_headline(manifest.get("task", ""))
    plan = manifest.get("plan") or {}

    lead = next((a for a in artifacts if a["role"] == SYNTHESIS_ROLE and not a.get("error")), None)
    plan_counts = _plan_counts(texts.get(SYNTHESIS_ROLE))

    n_advisors = len(plan.get("roles") or [])
    rules = plan.get("matched_rules") or []
    if rules:
        route_note = (
            f"Matched by rule{'s' if len(rules) != 1 else ''}: "
            + ", ".join(f"<code>{esc(r)}</code>" for r in rules) + "."
        )
    else:
        route_note = "No rule matched; routed to the default specialist."

    # Table of contents first — "who is on this" is the first question a reader has. Then the
    # story, in the order it actually happened: each advisor reasoned it through alone and took
    # real pushback, and only afterward did the Engagement Lead read everyone's finished work
    # and bring it together. The plan comes last because it's the destination, not the opener —
    # this page is meant to be read, not scanned for the verdict first.
    sections_html = [_toc(artifacts)]

    sections_html.append(
        '<div class="act"><p class="act-label">How each of us reasoned it through</p>'
        f'<p class="sub">{route_note} Each of us drafted independently, then one of us, acting '
        "as critic, read that draft alone and pushed back on it in writing &mdash; a real "
        "objection, not a rubber stamp. Click any of us to collapse once you&#x27;ve read it.</p>"
    )
    for a in artifacts:
        role = a["role"]
        if role == SYNTHESIS_ROLE:
            continue
        if a.get("error"):
            sections_html.append(_absent_section(role, a))
            continue
        sections_html.append(_advisor_story(role, a, texts[role]))
    sections_html.append("</div>")  # .act

    if lead:
        sections_html.append(
            '<div class="act"><p class="act-label">Bringing it together</p>'
            '<p class="sub">Once every one of us above had finished, our Engagement Lead read '
            f"all {n_advisors} of our positions in full &mdash; this is where our "
            "disagreements actually surface, and where one plan gets built from "
            "what we each concluded.</p>"
        )
        sections_html.append(_synthesis_section(lead, texts[SYNTHESIS_ROLE]))
        sections_html.append("</div>")  # .act

    sections_html.append(_decision_bar(manifest))

    if headline:
        task_html = f'<h1 class="task">{esc(headline)}</h1>\n'
        if context:
            task_html += f'<p class="task-context">{esc(context)}</p>'
    else:
        # No sentence in the task was actually pithy (see PITHY_MAX_CHARS) — the honest fallback
        # is to stop pretending display type fits it, not to invent a shorter paraphrase.
        task_html = (
            '<div class="quote"><div class="lbl">The task</div>'
            f"<p>{esc(context)}</p></div>"
        )

    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>HuminLoop &mdash; Run {esc(manifest.get('run_id', ''))}</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@500;700&family=Inter:wght@400;500;600&display=swap">
<style>{CSS}</style>
<script>
(function(){{
  var THEME_KEY = "huminloop-theme";
  var saved;
  try {{ saved = localStorage.getItem(THEME_KEY); }} catch (e) {{}}
  document.documentElement.setAttribute("data-theme", saved === "dark" ? "dark" : "light");
}})();
</script>
</head>
<body>
<div class="wrap">
<header>
<div class="topbar">
<div class="brandmark">
<span class="loop-mark" aria-hidden="true"></span><span class="brand-word">HuminLoop Agents</span>
</div>
<button type="button" id="theme-toggle" class="theme-toggle" aria-pressed="false">Dark mode</button>
</div>
<div class="rid">
<span>Run {esc(manifest.get('run_id', ''))}</span>
<span>{esc(manifest.get('provider', ''))}</span>
<span>{esc((manifest.get('created_at') or '')[:10])}</span>
</div>
<p class="orient">This is the story of how we reasoned through one task: who we dispatched,
what each of us concluded on our own, the real pushback each of us took, why we revised in
response, where we disagreed with each other, and the plan our Engagement Lead built once we
had all finished. Nothing goes out until you read it and put your name
on it.</p>
{task_html}
{_summary_line(manifest, plan_counts)}
</header>
<main>
{"".join(sections_html)}
</main>
</div>
<script>
(function(){{
  var THEME_KEY = "huminloop-theme";
  var root = document.documentElement;
  var btn = document.getElementById("theme-toggle");
  function label(theme){{
    btn.textContent = theme === "dark" ? "Light mode" : "Dark mode";
    btn.setAttribute("aria-pressed", theme === "dark" ? "true" : "false");
  }}
  label(root.getAttribute("data-theme"));
  btn.addEventListener("click", function(){{
    var next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
    root.setAttribute("data-theme", next);
    label(next);
    try {{ localStorage.setItem(THEME_KEY, next); }} catch (e) {{}}
  }});
}})();
</script>
</body>
</html>
"""
