"""Render an approved run's manifest and artifacts into the DESIGN.md HTML report.

The CSS below is a direct copy of docs/design/run-renderer-reference.html — the approved
"Institutional Briefing" system. If the two ever disagree, the reference file is the source of
truth; this module's CSS constant should be updated to match it, never the other way round.

Only approved runs are supported. Rejected, pending and errored-run states are visually
undecided (see DESIGN.md "Not yet decided") and rendering one would be inventing a design this
project has not actually settled on.
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
  --ground:#fcfcfb;
  --panel:#f4f6f5;
  --ink:#181a19;
  --ink-2:#3d443f;
  --muted:#6e756f;
  --faint:#9aa19b;
  --rule:#dfe2e0;
  --rule-soft:#eaedeb;
  --accent:#1d5240;
  --accent-ink:#123528;
  --accent-wash:#eef3f0;
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --ground:#131615;
    --panel:#1a1e1c;
    --ink:#e9ece9;
    --ink-2:#c2c8c3;
    --muted:#8d948e;
    --faint:#6a716b;
    --rule:#2a302c;
    --rule-soft:#212623;
    --accent:#78c3a0;
    --accent-ink:#9fd8bb;
    --accent-wash:#18231e;
  }
}
:root[data-theme="dark"]{
  --ground:#131615;
  --panel:#1a1e1c;
  --ink:#e9ece9;
  --ink-2:#c2c8c3;
  --muted:#8d948e;
  --faint:#6a716b;
  --rule:#2a302c;
  --rule-soft:#212623;
  --accent:#78c3a0;
  --accent-ink:#9fd8bb;
  --accent-wash:#18231e;
}
*{box-sizing:border-box}
body{
  margin:0;
  background:var(--ground);
  color:var(--ink);
  font-family:"Public Sans",-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
  font-size:16px;
  line-height:1.7;
  -webkit-font-smoothing:antialiased;
}
a{color:var(--accent-ink)}
a:hover{color:var(--accent)}
:focus-visible{outline:2px solid var(--accent);outline-offset:3px;border-radius:2px}
code{
  font-family:ui-monospace,"SF Mono",Menlo,monospace;
  background:var(--panel);padding:2px 6px;font-size:.88em;
}
.wrap{max-width:1180px;margin:0 auto;padding:clamp(32px,5vw,72px) clamp(20px,4vw,56px) 120px}
.rid{
  font-size:11px;letter-spacing:.18em;text-transform:uppercase;
  color:var(--muted);font-weight:600;
  font-variant-numeric:tabular-nums;
  display:flex;flex-wrap:wrap;gap:6px 14px;
}
.rid span::after{content:" \\00b7";color:var(--faint)}
.rid span:last-child::after{content:""}
.orient{
  margin:18px 0 0;max-width:66ch;
  font-family:"Spectral",Georgia,serif;font-weight:300;
  font-size:17px;line-height:1.66;color:var(--ink-2);
}
.flow{
  list-style:none;margin:0;padding:0;
  display:flex;flex-wrap:wrap;gap:0;
  border-top:1px solid var(--rule);border-bottom:1px solid var(--rule);
}
.flow li{
  display:flex;flex-direction:column;gap:3px;
  padding:13px 26px 13px 0;margin-right:26px;
  position:relative;
}
.flow li::after{
  content:"";position:absolute;right:0;top:50%;
  width:9px;height:9px;margin-top:-5px;
  border-top:1px solid var(--faint);border-right:1px solid var(--faint);
  transform:rotate(45deg);
}
.flow li:last-child{margin-right:0;padding-right:0}
.flow li:last-child::after{display:none}
.flow .step{
  font-size:10px;letter-spacing:.16em;text-transform:uppercase;
  color:var(--muted);font-weight:700;
}
.flow .val{font-size:14px;color:var(--ink-2);white-space:nowrap}
.flow .val b{color:var(--ink);font-weight:600}
.flow li.terminal .val b{color:var(--accent-ink)}
@media (max-width:700px){
  .flow li{padding:11px 20px 11px 0;margin-right:20px}
  .flow .val{font-size:13px}
}
h1.task{
  font-family:"Spectral",Georgia,serif;
  font-weight:300;
  font-size:clamp(28px,4.4vw,42px);
  line-height:1.22;
  letter-spacing:-.015em;
  margin:22px 0 14px;
  max-width:22ch;
  text-wrap:balance;
}
.task-context{
  margin:0 0 30px;max-width:68ch;
  font-size:15px;line-height:1.6;color:var(--ink-2);
}
.gate{
  margin-top:28px;
  background:var(--accent-wash);
  border-left:4px solid var(--accent);
  padding:18px 24px;
  display:flex;flex-wrap:wrap;gap:8px 20px;align-items:baseline;
}
.gate .verdict{
  font-size:13px;font-weight:700;letter-spacing:.15em;
  color:var(--accent-ink);
}
.gate .who{font-size:16px;font-weight:600}
.gate .when{font-size:13px;color:var(--muted);font-variant-numeric:tabular-nums}
.gate .note{
  flex-basis:100%;margin:4px 0 0;
  font-family:"Spectral",Georgia,serif;font-weight:300;font-size:16px;
  color:var(--ink-2);
}
.gate.forced{
  border-left-color:#8a5a12;background:transparent;
  border:1px solid #8a5a12;border-left-width:4px;
}
.gate.forced .verdict{color:#8a5a12}
.gate .forced-tag{
  font-size:11px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;
  color:#8a5a12;border:1px solid #8a5a12;padding:2px 8px;
}
.body{
  display:grid;grid-template-columns:190px minmax(0,1fr);
  gap:56px;margin-top:52px;align-items:start;
}
nav.index{
  position:sticky;top:24px;display:flex;flex-direction:column;font-size:14px;
  max-height:calc(100vh - 48px);overflow-y:auto;
}
nav.index .grp{
  font-size:10px;letter-spacing:.18em;text-transform:uppercase;
  color:var(--faint);font-weight:700;margin:20px 0 4px;padding-left:15px;
}
nav.index .grp:first-child{margin-top:0}
nav.index a{
  display:flex;align-items:center;min-height:44px;
  padding:2px 0 2px 15px;
  border-left:1px solid var(--rule);
  color:var(--ink-2);text-decoration:none;
}
nav.index a:hover{border-left-color:var(--accent);color:var(--ink)}
nav.index a[aria-current="true"]{
  border-left:2px solid var(--accent);color:var(--ink);font-weight:600;
}
nav.index a.lead{font-weight:600;color:var(--ink)}
section{margin:0 0 52px;scroll-margin-top:24px}
h2{
  font-family:"Spectral",Georgia,serif;font-weight:400;
  font-size:26px;letter-spacing:-.01em;margin:0 0 4px;
  display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;
}
h2 .kind{
  font-family:"Public Sans",sans-serif;font-size:12px;font-weight:600;
  letter-spacing:.14em;text-transform:uppercase;color:var(--faint);
}
.sub{font-size:14px;color:var(--muted);margin:0 0 26px;max-width:70ch}
.quote{background:var(--panel);padding:20px 24px;margin:0 0 18px;max-width:74ch}
.quote .lbl{
  font-size:10px;letter-spacing:.18em;text-transform:uppercase;
  color:var(--muted);font-weight:700;margin-bottom:8px;
}
.quote p{
  margin:0;font-family:"Spectral",Georgia,serif;font-weight:300;
  font-size:17px;line-height:1.72;color:var(--ink-2);
}
.finding{padding:26px 0;border-top:1px solid var(--rule-soft)}
.fhead{display:flex;align-items:baseline;gap:14px;flex-wrap:wrap;font-size:12px}
.n{font-weight:700;color:var(--faint);font-size:15px;font-variant-numeric:tabular-nums}
.sev{letter-spacing:-2px;color:var(--accent);font-family:ui-monospace,monospace}
.sev-word{font-weight:700;text-transform:uppercase;letter-spacing:.09em}
.dim{
  color:var(--muted);text-transform:uppercase;letter-spacing:.09em;font-weight:600;
  border:1px solid var(--rule);padding:1px 8px;
}
.disp{margin-left:auto;color:var(--muted)}
.claim{margin:14px 0 0;max-width:70ch;color:var(--ink)}
.answer{margin-top:18px;padding-left:22px;border-left:2px solid var(--rule);max-width:68ch}
.answer .lbl{
  font-size:10px;letter-spacing:.18em;text-transform:uppercase;
  color:var(--muted);font-weight:700;
}
.answer p{margin:6px 0 0;color:var(--ink-2)}
.register{margin:0 0 40px}
.register:last-child{margin-bottom:0}
.register-head{display:flex;align-items:baseline;gap:12px;margin:0 0 4px}
.register-head h3{
  font-family:"Public Sans",sans-serif;font-size:12px;font-weight:700;
  letter-spacing:.14em;text-transform:uppercase;color:var(--muted);margin:0;
}
.register-count{font-size:12px;color:var(--faint);font-variant-numeric:tabular-nums}
.reg-item{padding:18px 0;border-top:1px solid var(--rule-soft);display:flex;gap:16px}
.reg-item .n{flex-shrink:0}
.reg-item p{margin:0;max-width:68ch;color:var(--ink)}
.reg-item .owner{
  display:inline-flex;align-items:baseline;gap:6px;margin-top:8px;
  font-size:13px;color:var(--muted);
}
.reg-item .owner b{color:var(--accent-ink);font-weight:600}
.reg-item.escalation p,.reg-item.disagreement p{
  font-family:"Spectral",Georgia,serif;font-weight:300;
  font-size:16px;color:var(--ink-2);line-height:1.7;
}
details.artifact{border-top:1px solid var(--rule);border-bottom:1px solid var(--rule)}
details.artifact summary{
  list-style:none;cursor:pointer;
  display:flex;align-items:center;gap:12px;flex-wrap:wrap;
  min-height:44px;padding:14px 0;font-weight:600;font-size:15px;
}
details.artifact summary::-webkit-details-marker{display:none}
details.artifact summary::before{content:"\\25b8";color:var(--faint);font-size:13px}
details.artifact[open] summary::before{content:"\\25be"}
details.artifact summary .meta{
  margin-left:auto;font-weight:400;font-size:13px;color:var(--muted);
  font-variant-numeric:tabular-nums;
}
details.artifact .doc{
  padding:4px 0 24px;max-width:70ch;
  font-family:"Spectral",Georgia,serif;font-weight:300;font-size:17px;line-height:1.74;
  color:var(--ink-2);
}
details.artifact .doc h4{
  font-family:"Public Sans",sans-serif;font-size:11px;letter-spacing:.16em;
  text-transform:uppercase;color:var(--muted);margin:22px 0 6px;font-weight:700;
}
details.artifact .doc ol,details.artifact .doc ul{margin:0;padding-left:1.3em}
details.artifact .doc li{margin:0 0 8px}
.gov{font-size:14px;color:var(--muted);margin:16px 0 0}
.gov b{color:var(--ink)}
.absent{
  padding:20px 24px;background:var(--panel);max-width:74ch;
  font-size:15px;color:var(--ink-2);
}
.decision{border-top:2px solid var(--accent);padding-top:26px}
.decision.forced{border-top-color:#8a5a12}
.decision .verdict{font-size:13px;font-weight:700;letter-spacing:.16em;color:var(--accent-ink)}
.decision.forced .verdict{color:#8a5a12}
.decision .who{font-family:"Spectral",Georgia,serif;font-size:32px;font-weight:400;margin-top:10px}
.decision .when{font-size:13px;color:var(--muted);margin-top:4px;font-variant-numeric:tabular-nums}
.decision .note{
  font-family:"Spectral",Georgia,serif;font-weight:300;font-size:17px;
  margin:18px 0 0;max-width:60ch;color:var(--ink-2);
}
.decision .force-note{margin-top:14px;font-size:13px;color:#8a5a12;font-weight:600;max-width:60ch}
.hash{font-family:ui-monospace,monospace;font-size:12px;color:var(--faint);margin-top:20px;word-break:break-all}
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


def split_headline(task: str) -> tuple[str, str]:
    """A pithy h1 plus supporting detail, built from the task's own sentences — never a
    paraphrase. Prefers a trailing question (usually the actual ask); falls back to the leading
    sentence when the task doesn't end that way, or to the whole task when it is one sentence.
    """
    task = (task or "").strip()
    sentences = [s.strip() for s in _SENTENCE_RE.split(task) if s.strip()]
    if len(sentences) > 1 and sentences[-1].endswith("?"):
        return sentences[-1], " ".join(sentences[:-1])
    if len(sentences) > 1:
        return sentences[0], " ".join(sentences[1:])
    return task, ""


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


def _governance_summary(artifacts: list[dict]) -> str:
    flagged = flagged_roles(artifacts)
    return "Approve" if not flagged else f"{len(flagged)} flagged"


def _flow_strip(manifest: dict) -> str:
    plan = manifest.get("plan") or {}
    artifacts = manifest.get("artifacts") or []
    rules = plan.get("matched_rules") or []
    if not rules:
        route_val = "<b>default</b>"
    elif len(rules) <= 2:
        route_val = "rule " + ", ".join(f"<b>{esc(r)}</b>" for r in rules)
    else:
        route_val = f"<b>{len(rules)} rules</b> matched"
    n_specialists = len(plan.get("roles") or [])
    n_findings = sum(
        len((a.get("critique") or {}).get("points") or [])
        for a in artifacts
        if a.get("role") != SYNTHESIS_ROLE
    )
    has_synthesis = any(a.get("role") == SYNTHESIS_ROLE and not a.get("error") for a in artifacts)
    decision = manifest.get("decision") or {}
    forced = bool(decision.get("forced"))
    gate_val = "Released &mdash; forced" if forced else "Released"

    steps = [
        ("Route", route_val),
        ("Draft", f"<b>{n_specialists}</b> advisor{'s' if n_specialists != 1 else ''}"),
        ("Challenge", f"<b>{n_findings}</b> finding{'s' if n_findings != 1 else ''}"),
    ]
    if has_synthesis:
        steps.append(("Synthesize", "<b>Engagement Lead</b>"))
    steps.append(("Governance", f"<b>{esc(_governance_summary(artifacts))}</b>"))

    lis = "\n".join(
        f'<li><span class="step">{s}</span><span class="val">{v}</span></li>' for s, v in steps
    )
    lis += (
        f'\n<li class="terminal"><span class="step">Gate</span>'
        f'<span class="val">{gate_val}</span></li>'
    )
    return f'<ol class="flow" aria-label="What happened in this run">{lis}</ol>'


def _decision_bar(manifest: dict, *, closing: bool) -> str:
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
    rows = ['<div class="grp">Run</div>', '<a href="#routing" aria-current="true">Routing</a>']
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
    lead = next((a for a in artifacts if a["role"] == SYNTHESIS_ROLE and not a.get("error")), None)
    if lead:
        rows.append('<div class="grp">Engagement Lead</div>')
        rows.append('<a href="#synthesis" class="lead">Synthesis</a>')
    rows.append('<div class="grp">Gate</div>')
    rows.append('<a href="#decision">Decision</a>')
    return f'<nav class="index" aria-label="Sections of this run">{"".join(rows)}</nav>'


_SEV_GLYPH = {"blocking": "&#9632;&#9632;&#9632;", "serious": "&#9632;&#9632;", "minor": "&#9632;"}


def _critique_section(role: str, critique: dict) -> str:
    title = esc(get_role(role).title)
    points = critique.get("points") or []
    accepted = sum(1 for p in points if p.get("disposition") == "accepted")
    parts = [
        f'<section id="c-{_slug(role)}">',
        f'<h2>{title} <span class="kind">Critique</span></h2>',
        f'<p class="sub">Someone pushed back on this draft {len(points)} time'
        f'{"s" if len(points) != 1 else ""}. {accepted} landed'
        f'{" and it got rewritten" if accepted else ""}.</p>',
    ]
    if critique.get("steelman"):
        parts.append(
            '<div class="quote"><div class="lbl">The strongest case for it</div>'
            f"<p>{esc(critique['steelman'])}</p></div>"
        )
    if critique.get("premortem"):
        parts.append(
            '<div class="quote"><div class="lbl">How this could go wrong</div>'
            f"<p>{esc(critique['premortem'])}</p></div>"
        )
    for i, p in enumerate(points, 1):
        sev = (p.get("severity") or "minor").lower()
        parts.append(
            '<article class="finding"><div class="fhead">'
            f'<span class="n">{i}</span>'
            f'<span class="sev" aria-hidden="true">{_SEV_GLYPH.get(sev, "&#9632;")}</span>'
            f'<span class="sev-word">{esc(sev)}</span>'
            f'<span class="dim">{esc(p.get("dimension", ""))}</span>'
            f'<span class="disp">{esc((p.get("disposition") or "pending").title())}</span>'
            "</div>"
            f'<p class="claim">{esc(p.get("claim", ""))}</p>'
        )
        if p.get("response"):
            parts.append(
                '<div class="answer"><div class="lbl">They answered</div>'
                f'<p>{esc(p["response"])}</p></div>'
            )
        parts.append("</article>")
    parts.append("</section>")
    return "\n".join(parts)


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


def _register_group(name: str, entries: list[str], *, item_class: str = "") -> str:
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
    return (
        '<div class="register"><div class="register-head">'
        f"<h3>{esc(name)}</h3>"
        f'<span class="register-count">{count_label}</span></div>'
        f'{"".join(items)}</div>'
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
        '<section id="synthesis">',
        '<h2>Engagement Lead <span class="kind">Synthesis</span></h2>',
        '<p class="sub">Reads every advisor artifact in full and reports what it recommends, '
        "where the advisors disagreed, and what only a person can decide. This is the one "
        "deliverable the client acts on.</p>",
    ]
    if recommendation:
        parts.append(
            '<div class="quote"><div class="lbl">Recommendation</div>'
            f"<p>{esc(recommendation)}</p></div>"
        )
    parts.append(_register_group("Decisions", regs.get("decisions") or []))
    parts.append(
        _register_group(
            "Disagreements", regs.get("disagreements") or [], item_class="disagreement"
        )
    )
    parts.append(
        _register_group("Escalations", regs.get("escalations") or [], item_class="escalation")
    )
    parts.append("</section>")
    return "\n".join(parts)


def render_run(manifest: dict, run_dir: Path) -> str:
    """Render one approved run to a self-contained HTML page matching DESIGN.md."""
    if manifest.get("status") != "approved":
        raise RenderError(
            f"run '{manifest.get('run_id')}' is {manifest.get('status')!r}, not approved; "
            "only approved runs can be rendered"
        )
    verify_artifacts(run_dir, manifest)  # refuse to render if bytes were tampered post-decision

    artifacts = manifest.get("artifacts") or []
    texts = {
        a["role"]: (run_dir / a["file"]).read_text(encoding="utf-8")
        for a in artifacts
        if not a.get("error") and a.get("file")
    }
    headline, context = split_headline(manifest.get("task", ""))
    plan = manifest.get("plan") or {}

    sections_html = ['<section id="routing"><h2>Routing</h2><p class="sub">']
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

    lead = next((a for a in artifacts if a["role"] == SYNTHESIS_ROLE and not a.get("error")), None)
    if lead:
        sections_html.append(_synthesis_section(lead, texts[SYNTHESIS_ROLE]))

    sections_html.append(_decision_bar(manifest, closing=True))

    context_html = f'<p class="task-context">{esc(context)}</p>' if context else ""

    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>HuminLoop &mdash; Run {esc(manifest.get('run_id', ''))}</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Spectral:ital,wght@0,300;0,400;0,600;1,300&family=Public+Sans:wght@400;500;600;700&display=swap">
<style>{CSS}</style>
</head>
<body>
<div class="wrap">
<header>
<div class="rid">
<span>HuminLoop</span>
<span>Run {esc(manifest.get('run_id', ''))}</span>
<span>{esc(manifest.get('provider', ''))}</span>
<span>{esc((manifest.get('created_at') or '')[:10])}</span>
</div>
<p class="orient">A team of AI advisors that argues with itself on purpose. Each one drafts, a
critic pushes back on the record, and the Engagement Lead reads every artifact in full before
reporting what it recommends. Nothing goes out until a person reads it and puts their name on
it.</p>
<h1 class="task">{esc(headline)}</h1>
{context_html}
{_flow_strip(manifest)}
{_decision_bar(manifest, closing=False)}
</header>
<div class="body">
{_nav(artifacts)}
<main>
{"".join(sections_html)}
</main>
</div>
</div>
</body>
</html>
"""
