"""Render a run's manifest and artifacts into the DESIGN.md HTML report.

v0.17.0 replaced the "Institutional Briefing" audit-record system with a dashboard: Tony's own
reaction to the first version ("I don't know who they are," "I would never show anybody this")
was correct and specific, and it named a different brief than the one the CSS below was built
to. See DESIGN.md's "The pivot" for the full account. This is now the source of truth for the
visual system — the old reference file is historical, not authoritative.

Approved and pending runs are both supported. Pending is the review surface: the consulting
lead reads the same page — the debate, every advisor's contribution, the Team's Plan — and acts
from the exact CLI commands the decision section prints, rather than reading a terminal
`show` dump first. Rejected and errored-run states remain visually undecided (see DESIGN.md
"Not yet decided") and rendering one would be inventing a design this project has not actually
settled on.
"""

import html
import re
from pathlib import Path

from .gate import verify_artifacts
from .governance import REQUIRED_SECTIONS, flagged_roles, split_sections
from .orchestrator import SYNTHESIS_ROLE, parse_registers
from .roles import get_role

CSS = """
:root{
  --page:#f9f9f7;
  --surface:#fcfcfb;
  --surface-2:#f2f2ef;
  --ink:#0b0b0b;
  --ink-2:#52514e;
  --muted:#898781;
  --rule:#e1e0d9;
  --rule-soft:#ececea;
  --accent:#2a78d6;
  --accent-ink:#184f95;
  --accent-wash:#eaf1fb;
  --good:#0ca30c;
  --good-wash:#e8f7e8;
  --warning:#c98500;
  --warning-ink:#8a5a12;
  --warning-wash:#fdf1da;
  --critical:#c23333;
  --critical-wash:#fbe9e8;
  --avatar-ink:#ffffff;
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --page:#0d0d0d;
    --surface:#1a1a19;
    --surface-2:#212120;
    --ink:#ffffff;
    --ink-2:#c3c2b7;
    --muted:#9a9890;
    --rule:#2c2c2a;
    --rule-soft:#242422;
    --accent:#5b9fed;
    --accent-ink:#a9cdf5;
    --accent-wash:#152238;
    --good:#39c239;
    --good-wash:#173317;
    --warning:#fab219;
    --warning-ink:#fed07a;
    --warning-wash:#332708;
    --critical:#f0837f;
    --critical-wash:#341918;
  }
}
:root[data-theme="dark"]{
  --page:#0d0d0d;
  --surface:#1a1a19;
  --surface-2:#212120;
  --ink:#ffffff;
  --ink-2:#c3c2b7;
  --muted:#9a9890;
  --rule:#2c2c2a;
  --rule-soft:#242422;
  --accent:#5b9fed;
  --accent-ink:#a9cdf5;
  --accent-wash:#152238;
  --good:#39c239;
  --good-wash:#173317;
  --warning:#fab219;
  --warning-ink:#fed07a;
  --warning-wash:#332708;
  --critical:#f0837f;
  --critical-wash:#341918;
}
*{box-sizing:border-box}
body{
  margin:0;
  background:var(--page);
  color:var(--ink);
  font-family:"Public Sans",-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
  font-size:16px;
  line-height:1.6;
  -webkit-font-smoothing:antialiased;
}
a{color:var(--accent-ink);text-decoration:none}
a:hover{color:var(--accent);text-decoration:underline}
:focus-visible{outline:2px solid var(--accent);outline-offset:3px;border-radius:2px}
code{
  font-family:ui-monospace,"SF Mono",Menlo,monospace;
  background:var(--surface-2);padding:2px 6px;font-size:.88em;border-radius:4px;
}
.wrap{max-width:1180px;margin:0 auto;padding:clamp(24px,4vw,56px) clamp(20px,4vw,56px) 120px}

/* ---- header ---- */
.topbar{display:flex;justify-content:space-between;align-items:center;gap:16px;flex-wrap:wrap}
.rid{
  font-size:11px;letter-spacing:.14em;text-transform:uppercase;
  color:var(--muted);font-weight:700;
  font-variant-numeric:tabular-nums;
  display:flex;flex-wrap:wrap;gap:6px 14px;
}
.rid span::after{content:" \\00b7";color:var(--rule)}
.rid span:last-child::after{content:""}
.theme-toggle{
  appearance:none;border:1px solid var(--rule);background:var(--surface);color:var(--ink-2);
  font:inherit;font-size:13px;font-weight:600;padding:8px 14px;border-radius:8px;cursor:pointer;
  min-height:44px;
}
.theme-toggle:hover{border-color:var(--accent);color:var(--ink)}
.orient{
  margin:20px 0 0;max-width:70ch;
  font-size:16px;line-height:1.6;color:var(--ink-2);
}
h1.task{
  font-family:inherit;
  font-weight:700;
  font-size:clamp(26px,4vw,38px);
  line-height:1.18;
  letter-spacing:-.01em;
  margin:20px 0 6px;
  max-width:26ch;
  color:var(--ink);
  text-wrap:balance;
}
.task-context{
  margin:0 0 8px;max-width:72ch;
  font-size:15px;line-height:1.6;color:var(--ink-2);
}

/* ---- stat tiles ---- */
.stat-row{
  display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:2px;
  margin:26px 0 0;background:var(--rule);border:1px solid var(--rule);border-radius:12px;
  overflow:hidden;
}
.stat{
  background:var(--surface);padding:18px 20px;display:flex;flex-direction:column;gap:4px;
  min-height:88px;justify-content:center;
}
.stat-value{
  font-size:30px;font-weight:700;line-height:1;color:var(--ink);
  font-variant-numeric:tabular-nums;
}
.stat-value.warn{color:var(--warning-ink)}
.stat-value.crit{color:var(--critical)}
.stat-label{font-size:12px;color:var(--muted);font-weight:600;letter-spacing:.02em}
.stat-gate{justify-content:center}
.chip{
  display:inline-flex;align-items:center;gap:6px;padding:6px 12px;border-radius:999px;
  font-size:13px;font-weight:700;letter-spacing:.01em;width:fit-content;
}
.chip-pending{background:var(--surface-2);color:var(--ink-2);border:1px solid var(--rule)}
.chip-good{background:var(--good-wash);color:var(--good)}
.chip-warning{background:var(--warning-wash);color:var(--warning-ink)}
.chip-neutral{
  background:var(--surface-2);color:var(--ink-2);font-size:12px;font-weight:600;
  padding:4px 10px;margin-top:6px;
}

/* ---- layout ---- */
.body{
  display:grid;grid-template-columns:200px minmax(0,1fr);
  gap:44px;margin-top:40px;align-items:start;
}
nav.index{
  position:sticky;top:24px;display:flex;flex-direction:column;font-size:14px;
  max-height:calc(100vh - 48px);overflow-y:auto;
}
nav.index .grp{
  font-size:11px;letter-spacing:.1em;text-transform:uppercase;
  color:var(--muted);font-weight:700;margin:20px 0 4px;padding-left:15px;
}
nav.index .grp:first-child{margin-top:0}
nav.index a{
  display:flex;align-items:center;min-height:40px;
  padding:2px 0 2px 15px;
  border-left:2px solid var(--rule);
  color:var(--ink-2);text-decoration:none;font-weight:500;
}
nav.index a:hover{border-left-color:var(--accent);color:var(--ink)}
nav.index a[aria-current="true"]{
  border-left-color:var(--accent);color:var(--ink);font-weight:700;
}
nav.index a.lead{font-weight:700;color:var(--ink)}
section{margin:0 0 44px;scroll-margin-top:24px}
h2{
  font-family:inherit;font-weight:700;
  font-size:22px;letter-spacing:-.005em;margin:0 0 4px;
  display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;color:var(--ink);
}
h2 .kind{
  font-size:11px;font-weight:700;
  letter-spacing:.1em;text-transform:uppercase;color:var(--muted);
}
.sub{font-size:14px;color:var(--muted);margin:0 0 22px;max-width:70ch}
.section-divider{
  font-size:12px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;
  color:var(--muted);border-top:1px solid var(--rule);padding-top:18px;margin:0 0 36px;
}

/* ---- team roster ---- */
.roster{
  display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));
  gap:14px;margin:8px 0 0;padding:0;list-style:none;
}
.roster li{border:1px solid var(--rule);border-radius:12px;background:var(--surface)}
.roster a{
  display:flex;gap:14px;padding:16px;text-decoration:none;color:inherit;align-items:flex-start;
  border-radius:12px;
}
.roster a:hover{background:var(--surface-2)}
.avatar{
  flex-shrink:0;width:40px;height:40px;border-radius:50%;
  display:flex;align-items:center;justify-content:center;
  font-size:14px;font-weight:700;color:var(--avatar-ink);
}
.member-body{display:flex;flex-direction:column;gap:3px;min-width:0}
.member-name{font-weight:700;font-size:15px;color:var(--ink)}
.member-remit{font-size:13px;color:var(--muted);line-height:1.45}

/* ---- plan / registers ---- */
#plan{
  border:1px solid var(--rule);border-radius:14px;padding:28px 28px 8px;
  margin-bottom:36px;background:var(--surface);
}
#plan h2{font-size:26px}
.quote{
  background:var(--surface-2);padding:18px 20px;margin:0 0 16px;
  max-width:76ch;border-radius:10px;
}
.quote .lbl{
  font-size:11px;letter-spacing:.1em;text-transform:uppercase;
  color:var(--muted);font-weight:700;margin-bottom:8px;
}
.quote p{margin:0;font-size:15px;line-height:1.65;color:var(--ink-2)}
.quote ol{margin:0;padding-left:1.2em}
.quote li{font-size:15px;line-height:1.65;color:var(--ink-2);margin:0 0 8px}
.quote li:last-child{margin-bottom:0}
.register{margin:0 0 28px}
.register:last-child{margin-bottom:8px}
.register-head{display:flex;align-items:baseline;gap:10px;margin:0 0 4px}
.register-head h3{
  font-size:13px;font-weight:700;
  letter-spacing:.08em;text-transform:uppercase;color:var(--ink-2);margin:0;
}
.register-count{
  font-size:12px;font-weight:700;color:var(--ink-2);background:var(--surface-2);
  border-radius:999px;padding:2px 9px;
}
.register-disagreements .register-count{background:var(--warning-wash);color:var(--warning-ink)}
.register-escalations .register-count{background:var(--critical-wash);color:var(--critical)}
.register-note{font-size:13px;color:var(--muted);margin:2px 0 10px;max-width:68ch}
.reg-item{
  padding:12px 0;border-top:1px solid var(--rule-soft);display:flex;
  gap:14px;align-items:flex-start;
}
.reg-item .n{
  flex-shrink:0;display:flex;align-items:center;justify-content:center;
  min-width:26px;height:26px;border-radius:50%;
  font-weight:700;font-size:13px;background:var(--surface-2);color:var(--ink-2);
}
.register-disagreements .reg-item .n{background:var(--warning-wash);color:var(--warning-ink)}
.register-escalations .reg-item .n{background:var(--critical-wash);color:var(--critical)}
.reg-item p{margin:0 0 2px;max-width:68ch;color:var(--ink);font-size:15px;line-height:1.55}
.reg-item .owner{
  display:inline-flex;align-items:baseline;gap:6px;margin-top:4px;
  font-size:12px;color:var(--muted);
}
.reg-item .owner b{color:var(--accent-ink);font-weight:700}

/* ---- critique & artifact ---- */
details.critique-detail,details.artifact{
  border:1px solid var(--rule);border-radius:10px;background:var(--surface);
  margin-bottom:2px;
}
details.critique-detail summary,details.artifact summary{
  list-style:none;cursor:pointer;
  display:flex;align-items:center;gap:12px;flex-wrap:wrap;
  min-height:48px;padding:12px 16px;font-weight:600;font-size:14px;
}
details.critique-detail summary::-webkit-details-marker,
details.artifact summary::-webkit-details-marker{display:none}
details.critique-detail summary::before,details.artifact summary::before{
  content:"\\25b8";color:var(--muted);font-size:13px;
}
details.critique-detail[open] summary::before,details.artifact[open] summary::before{
  content:"\\25be";
}
details.critique-detail summary .meta,details.artifact summary .meta{
  margin-left:auto;font-weight:500;font-size:13px;color:var(--muted);
  font-variant-numeric:tabular-nums;
}
.critique-body{padding:0 16px 16px}
details.artifact .doc{
  padding:4px 0 8px;max-width:72ch;
  font-size:15px;line-height:1.65;
  color:var(--ink-2);
}
details.artifact .doc h4{
  font-size:11px;letter-spacing:.1em;
  text-transform:uppercase;color:var(--muted);margin:20px 0 6px;font-weight:700;
}
details.artifact .doc ol,details.artifact .doc ul{margin:0;padding-left:1.3em}
details.artifact .doc li{margin:0 0 8px}
.quote-inline{background:var(--surface-2);padding:14px 16px;margin:0 0 10px;border-radius:8px}
.quote-inline .lbl{
  font-size:10px;letter-spacing:.1em;text-transform:uppercase;
  color:var(--muted);font-weight:700;margin-bottom:6px;
}
.quote-inline p{margin:0;font-size:14px;line-height:1.6;color:var(--ink-2)}
.finding{padding:14px 0;border-top:1px solid var(--rule-soft)}
.finding:first-child{border-top:none}
.fhead{display:flex;align-items:center;gap:10px;flex-wrap:wrap;font-size:12px}
.n{font-weight:700;color:var(--muted);font-size:14px;font-variant-numeric:tabular-nums}
.sev-badge{
  font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;
  padding:3px 9px;border-radius:999px;
}
.sev-crit{background:var(--critical-wash);color:var(--critical)}
.sev-warn{background:var(--warning-wash);color:var(--warning-ink)}
.sev-info{background:var(--surface-2);color:var(--ink-2)}
.dim{
  color:var(--muted);text-transform:uppercase;letter-spacing:.05em;font-weight:600;
  font-size:11px;
}
.disp{margin-left:auto;font-size:12px;font-weight:700}
.disp-resolved{color:var(--good)}
.disp-open{color:var(--muted)}
.claim{margin:10px 0 0;max-width:72ch;color:var(--ink);font-size:15px;line-height:1.55}
.answer{
  margin-top:12px;padding:10px 14px;background:var(--good-wash);
  border-radius:8px;max-width:70ch;
}
.answer .lbl{
  font-size:10px;letter-spacing:.1em;text-transform:uppercase;
  color:var(--good);font-weight:700;
}
.answer p{margin:6px 0 0;color:var(--ink-2);font-size:14px}
.gov{font-size:13px;color:var(--muted);margin:10px 16px 0}
.gov b{color:var(--ink)}
.absent{
  padding:18px 20px;background:var(--warning-wash);max-width:76ch;
  font-size:14px;color:var(--ink);border-radius:10px;
}

/* ---- decision ---- */
.gate{
  margin-top:22px;
  background:var(--surface-2);
  border:1px solid var(--rule);border-radius:12px;
  padding:16px 20px;
  display:flex;flex-wrap:wrap;gap:8px 20px;align-items:center;
}
.gate .verdict{
  font-size:13px;font-weight:700;letter-spacing:.06em;
  color:var(--ink);
}
.gate .who{font-size:15px;font-weight:600;color:var(--ink-2)}
.gate .when{font-size:13px;color:var(--muted);font-variant-numeric:tabular-nums}
.gate .note{
  flex-basis:100%;margin:4px 0 0;
  font-size:15px;
  color:var(--ink-2);
}
.gate.forced{background:var(--warning-wash);border-color:var(--warning-ink)}
.gate.forced .verdict{color:var(--warning-ink)}
.gate .forced-tag{
  font-size:11px;font-weight:700;letter-spacing:.05em;text-transform:uppercase;
  color:var(--warning-ink);border:1px solid var(--warning-ink);padding:2px 8px;border-radius:999px;
}
.gate.pending{background:var(--accent-wash);border-color:var(--accent)}
.gate.pending .verdict{color:var(--accent-ink)}
.decision{
  border:1px solid var(--rule);border-radius:14px;padding:26px 28px;background:var(--surface);
}
.decision.forced{border-color:var(--warning-ink);background:var(--warning-wash)}
.decision.pending{border-color:var(--accent);background:var(--accent-wash)}
.decision .verdict{font-size:22px;font-weight:700;color:var(--ink)}
.decision.forced .verdict{color:var(--warning-ink)}
.decision.pending .verdict{color:var(--accent-ink)}
.decision .cta{
  font-size:15px;
  margin:12px 0 0;max-width:66ch;color:var(--ink-2);
}
.decision .cmd{
  margin-top:14px;display:flex;flex-direction:column;gap:8px;
  font-family:ui-monospace,"SF Mono",Menlo,monospace;font-size:13px;
}
.decision .cmd code{
  background:var(--surface);padding:10px 14px;display:block;max-width:76ch;
  overflow-x:auto;white-space:pre;border-radius:8px;border:1px solid var(--rule);
}
.decision .flag-list{
  margin-top:14px;font-size:13px;color:var(--warning-ink);font-weight:700;max-width:66ch;
}
.decision .who{font-size:28px;font-weight:700;margin-top:8px;color:var(--ink)}
.decision .when{font-size:13px;color:var(--muted);margin-top:4px;font-variant-numeric:tabular-nums}
.decision .note{
  font-size:15px;
  margin:14px 0 0;max-width:60ch;color:var(--ink-2);
}
.decision .force-note{
  margin-top:12px;font-size:13px;color:var(--warning-ink);
  font-weight:700;max-width:60ch;
}
.hash{font-family:ui-monospace,monospace;font-size:12px;color:var(--muted);margin-top:16px;word-break:break-all}
@media (max-width:880px){
  .body{grid-template-columns:1fr;gap:0}
  nav.index{
    position:static;flex-direction:row;gap:2px;max-height:none;
    overflow-x:auto;overflow-y:visible;border-bottom:1px solid var(--rule);
    margin-bottom:34px;padding-bottom:2px;
  }
  nav.index .grp{display:none}
  nav.index a{
    border-left:none;border-bottom:2px solid transparent;
    padding:0 14px;white-space:nowrap;
  }
  nav.index a[aria-current="true"]{border-left:none;border-bottom-color:var(--accent)}
}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
"""

_HTTPS_RE = re.compile(r"https://\S+")
_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")
_NUMBERED_LINE_RE = re.compile(r"^[ \t]*\d+[.)][ \t]*(.+)$")
_SECTION_LABELS = {
    "objective": "Objective",
    "body": "Body",
    "citations": "Citations",
    "risks": "Risks",
    "next steps": "Next Steps",
}


class RenderError(Exception):
    pass


def esc(text: str | None) -> str:
    return html.escape(text or "", quote=True)


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
    lis = "\n".join(f"<li>{_linkify(esc(item))}</li>" for item in items)
    return f"<ul>{lis}</ul>"


def _render_next_steps(body: str) -> str:
    lines = [ln.strip() for ln in body.splitlines() if ln.strip()]
    numbered = [_NUMBERED_LINE_RE.match(ln) for ln in lines]
    if lines and all(numbered):
        lis = "\n".join(f"<li>{esc(m.group(1))}</li>" for m in numbered)
        return f"<ol>{lis}</ol>"
    return "".join(f"<p>{esc(p)}</p>" for p in body.split("\n\n") if p.strip())


def _render_prose(body: str) -> str:
    return "".join(f"<p>{esc(p.strip())}</p>" for p in body.split("\n\n") if p.strip())


def artifact_doc_html(text: str) -> str:
    """The five-section envelope (Objective/Body/Citations/Risks/Next Steps), escaped and
    given light structure. No markdown is interpreted — DESIGN.md settles escaping, not
    rendering, and interpreting the model's own formatting choices is a bigger claim than an
    audit record should make about text nobody has reviewed for markup, only for content."""
    sections = split_sections(text)
    parts = []
    for key in REQUIRED_SECTIONS:
        body = sections.get(key, "")
        if not body:
            continue
        parts.append(f"<h4>{esc(_SECTION_LABELS[key])}</h4>")
        if key == "citations":
            parts.append(_render_citations(body))
        elif key == "next steps":
            parts.append(_render_next_steps(body))
        else:
            parts.append(_render_prose(body))
    return "\n".join(p for p in parts if p)


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


def _stat_tiles(manifest: dict, plan_counts: dict) -> str:
    """The numbers a reader needs in the first five seconds: how many advisors worked this,
    how much got challenged, where they disagreed, what needs a human. Severity gets color —
    disagreements amber, escalations red — because that is the one thing worth seeing before
    reading a word of prose."""
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
        gate_html = '<span class="chip chip-pending">Awaiting your decision</span>'
    elif forced:
        gate_html = '<span class="chip chip-warning">Approved &mdash; forced</span>'
    else:
        gate_html = '<span class="chip chip-good">Approved</span>'

    n_disagreements = plan_counts["disagreements"]
    n_escalations = plan_counts["escalations"]
    tiles = [
        ("Advisors dispatched", str(n_specialists), ""),
        (
            "Findings challenged",
            str(n_findings),
            "",
        ),
        ("Disagreements", str(n_disagreements), "warn" if n_disagreements else ""),
        ("Escalations to you", str(n_escalations), "crit" if n_escalations else ""),
    ]
    cells = "".join(
        f'<div class="stat"><div class="stat-value{" " + cls if cls else ""}">{esc(v)}</div>'
        f'<div class="stat-label">{esc(label)}</div></div>'
        for label, v, cls in tiles
    )
    cells += (
        '<div class="stat stat-gate"><div class="stat-value">'
        f"{gate_html}</div><div class=\"stat-label\">Gate</div></div>"
    )
    return f'<div class="stat-row" role="group" aria-label="This run at a glance">{cells}</div>'


def _pending_decision_bar(manifest: dict, *, closing: bool) -> str:
    """The review surface for a run nobody has decided yet.

    Not a smaller version of the decided bar — a different purpose. It never claims a verdict
    (there is none), and instead of a record it prints the exact commands that would act on
    what the reader just read, including the --force and --note a flagged role actually requires
    so the CTA never lies about how easy the decision in front of them is.
    """
    run_id = manifest.get("run_id", "")
    if not closing:
        return (
            '<div class="gate pending">\n'
            '<span class="verdict">AWAITING YOUR DECISION</span>\n'
            f'<span class="who">Run {esc(run_id)}</span>\n'
            "</div>"
        )
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
        "is above &mdash; every advisor's draft, what got challenged, and the Team's Plan at "
        "the top.</p>\n"
        '<div class="verdict">NOT YET DECIDED</div>\n'
        '<p class="cta">Act from here once you have read it:</p>\n'
        '<div class="cmd">\n'
        f"<code>{esc(approve_cmd)}</code>\n"
        f"<code>{esc(reject_cmd)}</code>\n"
        "</div>\n"
        f"{flag_html}\n"
        "</section>"
    )


def _decision_bar(manifest: dict, *, closing: bool) -> str:
    if manifest.get("status") == "pending":
        return _pending_decision_bar(manifest, closing=closing)
    decision = manifest.get("decision") or {}
    state = decision.get("state", "")
    forced = bool(decision.get("forced"))
    verdict = state.upper()
    if forced:
        verdict += " &mdash; FORCED" if closing else ""
    tag = "" if not (forced and not closing) else '<span class="forced-tag">Forced</span>'
    note = (
        f'<p class="note">&ldquo;{esc(decision.get("note", ""))}&rdquo;</p>'
        if decision.get("note")
        else ""
    )
    cls = "gate forced" if forced else "gate"
    if closing:
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
            '<p class="sub">Nothing here went anywhere until a person read it and said yes. '
            "Before recording that, the system re-read every document to check nothing had "
            "changed since they looked.</p>\n"
            f'<div class="verdict">{verdict}</div>\n'
            f'<div class="who">{esc(decision.get("by", ""))}</div>\n'
            f'<div class="when">{esc(decision.get("at", ""))}</div>\n'
            f"{note}\n{force_note}\n"
            f'<p class="hash">Artifacts verified at decision time &middot; {clean} artifact(s), '
            f'all sha256-checked &middot; forced: {str(forced).lower()} &middot; '
            f'flagged roles: {esc(", ".join(decision.get("flagged_roles") or []) or "none")}</p>\n'
            "</section>"
        )
    return (
        f'<div class="{cls}">\n'
        f'<span class="verdict">{verdict}</span>\n{tag}\n'
        f'<span class="who">{esc(decision.get("by", ""))}</span>\n'
        f'<span class="when">{esc(decision.get("at", ""))}</span>\n'
        f"{note}\n</div>"
    )


def _nav(artifacts: list[dict]) -> str:
    lead = next((a for a in artifacts if a["role"] == SYNTHESIS_ROLE and not a.get("error")), None)
    rows = ['<div class="grp">Start here</div>', '<a href="#team" aria-current="true">Team</a>']
    if lead:
        rows.append('<a href="#plan" class="lead">The Team&#x27;s Plan</a>')
    rows.append('<div class="grp">How the team got there</div>')
    rows.append('<a href="#routing">Routing</a>')
    for a in artifacts:
        role = a["role"]
        if role == SYNTHESIS_ROLE:
            continue
        title = esc(get_role(role).title)
        rows.append(f'<div class="grp">{title}</div>')
        if a.get("error"):
            rows.append(f'<a href="#a-{_slug(role)}">Status</a>')
            continue
        if a.get("critique"):
            n = len((a["critique"] or {}).get("points") or [])
            rows.append(f'<a href="#c-{_slug(role)}">Critique ({n})</a>')
        rows.append(f'<a href="#a-{_slug(role)}">Artifact</a>')
    rows.append('<div class="grp">Gate</div>')
    rows.append('<a href="#decision">Decision</a>')
    return f'<nav class="index" aria-label="Sections of this run">{"".join(rows)}</nav>'


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


def _team_roster(artifacts: list[dict]) -> str:
    """Who worked this engagement, at a glance, before the detail of what each one said.

    This was the sharpest miss in the first version: a role title and a one-line remit in gray
    text at the bottom of a wall of prose is not an answer to "who is on my team." A card per
    specialist — a colored initial, the title, the remit, and how many challenges it took and
    resolved — is the first thing on the page after the header, not something found by scrolling
    past the plan.
    """
    items = []
    for i, a in enumerate(artifacts):
        role = a["role"]
        r = get_role(role)
        href = "#plan" if role == SYNTHESIS_ROLE else f"#a-{_slug(role)}"
        color = _TEAM_COLORS[i % len(_TEAM_COLORS)]
        points = (a.get("critique") or {}).get("points") or []
        chip = ""
        if points:
            accepted = sum(1 for p in points if p.get("disposition") == "accepted")
            chip = (
                f'<span class="chip chip-neutral">{len(points)} challenged '
                f"&middot; {accepted} resolved</span>"
            )
        items.append(
            f'<li class="member"><a href="{href}">'
            f'<span class="avatar" style="background:{color}">{esc(_initials(r.title))}</span>'
            '<span class="member-body">'
            f'<span class="member-name">{esc(r.title)}</span>'
            f'<span class="member-remit">{esc(r.instruction)}</span>'
            f"{chip}</span></a></li>"
        )
    return (
        '<section id="team"><h2>Team on this engagement</h2>'
        '<p class="sub">Every seat dispatched for this task, and what it owns.</p>'
        f'<ul class="roster">{"".join(items)}</ul></section>'
    )


_SEV_STATUS = {"blocking": "crit", "serious": "warn", "minor": "info"}


def _critique_summary_line(critique: dict) -> str:
    points = critique.get("points") or []
    accepted = sum(1 for p in points if p.get("disposition") == "accepted")
    summary = f'{len(points)} challenge{"s" if len(points) != 1 else ""}'
    if points:
        summary += f" &middot; {accepted} resolved"
    return summary


def _critique_body_html(critique: dict) -> str:
    """The steelman, the pre-mortem, and every finding — shared between a specialist's own
    Critique section and the Engagement Lead's own critique, which the plan gets too (see
    orchestrator._do_synthesis) and which the old renderer never surfaced at all."""
    parts = []
    if critique.get("steelman"):
        parts.append(
            '<div class="quote-inline"><div class="lbl">The strongest case for it</div>'
            f"<p>{esc(critique['steelman'])}</p></div>"
        )
    if critique.get("premortem"):
        parts.append(
            '<div class="quote-inline"><div class="lbl">How this could go wrong</div>'
            f"<p>{esc(critique['premortem'])}</p></div>"
        )
    for i, p in enumerate(critique.get("points") or [], 1):
        sev = (p.get("severity") or "minor").lower()
        status = _SEV_STATUS.get(sev, "info")
        resolved = p.get("disposition") == "accepted"
        disp_cls = "disp-resolved" if resolved else "disp-open"
        disp_label = esc((p.get("disposition") or "pending").title())
        parts.append(
            '<article class="finding"><div class="fhead">'
            f'<span class="n">{i}</span>'
            f'<span class="sev-badge sev-{status}">{esc(sev.title())}</span>'
            f'<span class="dim">{esc(p.get("dimension", ""))}</span>'
            f'<span class="disp {disp_cls}">{disp_label}</span>'
            "</div>"
            f'<p class="claim">{esc(p.get("claim", ""))}</p>'
        )
        if p.get("response"):
            parts.append(
                '<div class="answer"><div class="lbl">They answered</div>'
                f'<p>{esc(p["response"])}</p></div>'
            )
        parts.append("</article>")
    return "\n".join(parts)


def _critique_section(role: str, critique: dict) -> str:
    """Collapsed by default, like the artifact below it — the summary line (count, resolved)
    is the thing worth seeing while scanning the page; the steelman/pre-mortem/findings are one
    click away, not a wall of text forced on every reader whether they asked for it or not."""
    title = esc(get_role(role).title)
    summary = _critique_summary_line(critique)
    return (
        f'<section id="c-{_slug(role)}">\n'
        f'<h2>{title} <span class="kind">Critique</span></h2>\n'
        '<details class="critique-detail">\n'
        f'<summary><span class="meta">{summary}</span></summary>\n'
        f'<div class="critique-body">{_critique_body_html(critique)}</div>\n'
        "</details></section>"
    )


def _artifact_section(role: str, artifact: dict, text: str) -> str:
    title = esc(get_role(role).title)
    n_chars = f"{len(text):,} chars"
    sha = artifact.get("sha256", "")
    meta = f"{n_chars} &middot; sha256 {esc(sha[:9])}&hellip;"
    if artifact.get("revised"):
        meta += " &middot; revised"
    verdict = ((artifact.get("review") or {}).get("verdict") or "").lower()
    issues = (artifact.get("review") or {}).get("issues") or []
    gov = "passed" if not issues else f"{len(issues)} issue(s)"
    return (
        f'<section id="a-{_slug(role)}">\n'
        f'<h2>{title} <span class="kind">Artifact</span></h2>\n'
        '<details class="artifact"><summary>Read the full artifact '
        f'<span class="meta">{meta}</span></summary>\n'
        f'<div class="doc">{artifact_doc_html(text)}</div>\n'
        "</details>\n"
        f'<p class="gov">Automated checks: <b>{esc(gov)}</b>'
        f'{" (verdict: " + esc(verdict) + ")" if verdict else ""}.</p>\n'
        "</section>"
    )


def _absent_section(role: str, artifact: dict) -> str:
    title = esc(get_role(role).title)
    return (
        f'<section id="a-{_slug(role)}">\n'
        f'<h2>{title} <span class="kind">Status</span></h2>\n'
        f'<div class="absent">This seat produced nothing. {esc(artifact.get("error", ""))}</div>\n'
        "</section>"
    )


def _register_group(name: str, entries: list[str], *, item_class: str = "", note: str = "") -> str:
    """`note` is a hardcoded explainer string this module wrote, not model output — rendered
    as-is (it already carries its own entities), never passed through esc()."""
    count_label = f"{len(entries)}" if entries else "None"
    items = []
    for i, entry in enumerate(entries, 1):
        cls = f"reg-item {item_class}".strip()
        if name == "Decisions":
            text, owner = _split_decision(entry)
            owner_html = f'<div class="owner">Owner: <b>{esc(owner)}</b></div>' if owner else ""
            items.append(
                f'<div class="{cls}"><span class="n">{i}</span>'
                f"<div><p>{esc(text)}</p>{owner_html}</div></div>"
            )
        else:
            items.append(f'<div class="{cls}"><span class="n">{i}</span><p>{esc(entry)}</p></div>')
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
        '<h2>The Team&#x27;s Plan</h2>',
        '<p class="sub">The Engagement Lead reads every advisor&#x27;s work in full and reports '
        "back: what the team recommends, what it decided, where advisors pushed back on each "
        "other before settling, and what only you can answer. This is the one deliverable you "
        "act on &mdash; everything after this section is how the team got here.</p>",
    ]
    if recommendation:
        parts.append(
            '<div class="quote"><div class="lbl">Recommendation</div>'
            f"<p>{esc(recommendation)}</p></div>"
        )
    parts.append(_register_group("Decisions", regs.get("decisions") or []))
    parts.append(
        _register_group(
            "Disagreements",
            regs.get("disagreements") or [],
            item_class="disagreement",
            note="Where advisors reached different conclusions and the Lead had to weigh them.",
        )
    )
    parts.append(
        _register_group(
            "Escalations",
            regs.get("escalations") or [],
            item_class="escalation",
            note=(
                "Questions no advisor can answer for you &mdash; each one is why this "
                "run needed your sign-off."
            ),
        )
    )
    next_steps = sections.get("next steps", "")
    if next_steps:
        parts.append(
            '<div class="register"><div class="register-head">'
            "<h3>Implementation &amp; Timeline</h3></div>"
            f'<div class="quote">{_render_next_steps(next_steps)}</div></div>'
        )
    risks = sections.get("risks", "")
    if risks:
        parts.append(
            '<div class="register"><div class="register-head"><h3>What Could Go Wrong</h3></div>'
            f'<div class="quote"><p>{esc(risks)}</p></div></div>'
        )
    lead_critique = artifact.get("critique")
    if lead_critique:
        # The plan gets challenged too — orchestrator._do_synthesis runs the same critique
        # loop on the Engagement Lead's synthesis as every specialist gets. The old renderer
        # never surfaced this at all; it's real debate, not a lesser or decorative addition.
        summary = _critique_summary_line(lead_critique)
        parts.append(
            '<details class="critique-detail plan-critique">\n'
            f'<summary><span class="meta">The plan itself was challenged &middot; {summary}'
            "</span></summary>\n"
            f'<div class="critique-body">{_critique_body_html(lead_critique)}</div>\n'
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

    # Team first: "who is on this" is the first question a reader has, not something found by
    # scrolling past the plan. The plan follows immediately after — still the one deliverable
    # to act on, just no longer the very first thing on the page.
    sections_html = [_team_roster(artifacts)]
    if lead:
        sections_html.append(_synthesis_section(lead, texts[SYNTHESIS_ROLE]))

    sections_html.append(
        '<p class="section-divider">How the team got there &mdash; each advisor&#x27;s draft, '
        "what got challenged, and what changed.</p>"
    )
    sections_html.append('<section id="routing"><h2>Routing</h2><p class="sub">')
    rules = plan.get("matched_rules") or []
    if rules:
        sections_html.append(
            f"Matched by rule{'s' if len(rules) != 1 else ''}: "
            + ", ".join(f"<code>{esc(r)}</code>" for r in rules)
            + f", dispatching {len(plan.get('roles') or [])} advisor(s)."
        )
    else:
        sections_html.append("No rule matched; routed to the default specialist.")
    sections_html.append("</p></section>")

    for a in artifacts:
        role = a["role"]
        if role == SYNTHESIS_ROLE:
            continue
        if a.get("error"):
            sections_html.append(_absent_section(role, a))
            continue
        if a.get("critique"):
            sections_html.append(_critique_section(role, a["critique"]))
        sections_html.append(_artifact_section(role, a, texts[role]))

    sections_html.append(_decision_bar(manifest, closing=True))

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
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Public+Sans:wght@400;500;600;700&display=swap">
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
<div class="rid">
<span>HuminLoop</span>
<span>Run {esc(manifest.get('run_id', ''))}</span>
<span>{esc(manifest.get('provider', ''))}</span>
<span>{esc((manifest.get('created_at') or '')[:10])}</span>
</div>
<button type="button" id="theme-toggle" class="theme-toggle" aria-pressed="false">Dark mode</button>
</div>
<p class="orient">A team of AI advisors that argues with itself on purpose. Each one drafts, a
critic pushes back on the record, and the Engagement Lead reads every artifact in full and
reports back. Below: who&#x27;s on the team, then the Team&#x27;s Plan &mdash; what they recommend,
decided, disagreed on, and need from you &mdash; then how each advisor got there. Nothing goes
out until a person reads it and puts their name on it.</p>
{task_html}
{_stat_tiles(manifest, plan_counts)}
{_decision_bar(manifest, closing=False)}
</header>
<div class="body">
{_nav(artifacts)}
<main>
{"".join(sections_html)}
</main>
</div>
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
