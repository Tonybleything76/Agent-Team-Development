"""A working dashboard for a run, not a document about it.

The narrative renderer answers "what happened". This answers "what do I do now", which is the
question you have with a client in front of you. Tabs, dense sections, everything findable in
one screen rather than a scroll.
"""

import re
from pathlib import Path

from .governance import split_sections
from .orchestrator import SYNTHESIS_ROLE, parse_registers
from .render import (
    esc,
    initials,
    mdlite,
    parse_milestones,
    precheck,
    pushback_rows,
    split_headline,
    staffing,
)

ESCALATION_PREFIX = "Escalated to the human:"
# Steps naming one of these read as the client's move, not yours.
CLIENT_MARKERS = (
    "client",
    "sponsor",
    "customer",
    "their ",
    "they ",
    "ops lead",
    "safety",
    "legal",
    "it/security",
    "stakeholder",
)

TABS = [
    ("overview", "Overview"),
    ("needs-you", "Needs you"),
    ("team", "Team"),
    ("debate", "Debate"),
    ("plan", "The plan"),
    ("actions", "Next steps"),
    ("docs", "Documents"),
]


def _steps(text: str) -> list[str]:
    """Numbered or bulleted steps out of a Next Steps block."""
    out = []
    for raw in (text or "").splitlines():
        line = raw.strip()
        line = re.sub(r"^(?:\d+[.)]|[-*•])\s*", "", line)
        if line:
            out.append(line)
    return out


def _is_client_step(step: str) -> bool:
    low = step.lower()
    return any(m in low for m in CLIENT_MARKERS)


def _tile(value, label, tone="") -> str:
    return (
        f'<div class="tile {tone}"><span class="tile-v">{esc(str(value))}</span>'
        f'<span class="tile-l">{esc(label)}</span></div>'
    )


def _escalations(artifacts: list[dict]) -> list[str]:
    out = []
    for a in artifacts:
        for flag in a.get("process_flags") or []:
            if flag.startswith(ESCALATION_PREFIX):
                out.append(flag[len(ESCALATION_PREFIX) :].strip())
    return out


def _bar(segments: list[tuple[int, str, str]]) -> str:
    """A proportional bar. segments: (count, css class, label). Nothing to read; a shape."""
    total = sum(c for c, _, _ in segments) or 1
    fills = "".join(
        f'<span class="seg {cls}" style="width:{c / total * 100:.1f}%" title="{esc(label)}: {c}">'
        f"</span>"
        for c, cls, label in segments
        if c
    )
    keys = "".join(
        f'<span class="key"><i class="{cls}"></i>{c} {esc(label)}</span>'
        for c, cls, label in segments
        if c
    )
    return f'<div class="bar">{fills}</div><div class="keys">{keys}</div>'


def _donut(part: int, whole: int, label: str) -> str:
    """One number worth seeing as a shape rather than reading as a fraction."""
    whole = whole or 1
    pct = part / whole
    circumference = 2 * 3.14159 * 26
    return (
        f'<div class="donut"><svg viewBox="0 0 64 64" width="76" height="76">'
        f'<circle cx="32" cy="32" r="26" class="ring-bg"/>'
        f'<circle cx="32" cy="32" r="26" class="ring-fg" '
        f'stroke-dasharray="{circumference * pct:.1f} {circumference:.1f}" '
        f'transform="rotate(-90 32 32)"/>'
        f'<text x="32" y="37" class="ring-t">{part}</text></svg>'
        f'<span class="donut-l">{esc(label)}</span></div>'
    )


def _people(dispatched: list[dict], absent: list[dict]) -> str:
    """The roster as faces, not a table: who is on, who is on the bench."""

    def chip(item, on):
        title = item["title"]
        sub = item.get("why") if on else item.get("would_join_on", "")
        return (
            f'<div class="person {"on" if on else "off"}" title="{esc(sub)}">'
            f'<span class="av">{esc(initials(title))}</span>'
            f'<span class="pn">{esc(title)}</span></div>'
        )

    on = "".join(chip(d, True) for d in dispatched)
    off = "".join(chip(a, False) for a in absent)
    return (
        f'<div class="people">{on}</div>'
        f"<h3>On the bench &mdash; hover to see what would call them in</h3>"
        f'<div class="people bench">{off}</div>'
    )


def _timeline(steps: list[str]) -> str:
    if not steps:
        return ""
    items = "".join(
        f'<li><span class="dot">{i}</span><div>{mdlite(s)}</div></li>'
        for i, s in enumerate(steps, 1)
    )
    return f'<ol class="timeline">{items}</ol>'


def _card(title: str, body: str, *, tone: str = "", foot: str = "") -> str:
    foot_html = f'<div class="card-foot">{foot}</div>' if foot else ""
    return (
        f'<div class="card {tone}"><h4>{esc(title)}</h4><div class="card-body">{body}</div>'
        f"{foot_html}</div>"
    )


def _overview(manifest, lead_sections, regs, artifacts, pushbacks, escalations) -> str:
    rec = lead_sections.get("objective") or "No recommendation was produced."
    blocked = bool(escalations)
    tiles = "".join(
        [
            _tile(len([a for a in artifacts if a["role"] != SYNTHESIS_ROLE]), "advisors"),
            _tile(len(pushbacks), "challenges"),
            _tile(sum(1 for p in pushbacks if p["disposition"] == "accepted"), "accepted"),
            _tile(len(regs.get("disagreements") or []), "disagreements"),
            _tile(len(escalations), "need you", "warn" if blocked else ""),
        ]
    )
    gate = (
        f'<div class="banner warn"><b>{len(escalations)} question(s) are yours to answer.</b> '
        "Until they are, approving this run requires an explicit override.</div>"
        if blocked
        else '<div class="banner ok">Nothing is blocking. This run can be approved.</div>'
    )
    sev = [
        (sum(1 for p in pushbacks if p["severity"] == "blocking"), "s-block", "blocking"),
        (sum(1 for p in pushbacks if p["severity"] == "serious"), "s-serious", "serious"),
        (sum(1 for p in pushbacks if p["severity"] == "minor"), "s-minor", "minor"),
    ]
    accepted = sum(1 for p in pushbacks if p["disposition"] == "accepted")
    read = manifest.get("context_read") or []
    # A chip says what became of one file. Anything other than "read" carries the state as a
    # WORD, not only as a colour: DESIGN.md's rule is that status colour never means anything
    # on its own, and a refused symlink that merely looks slightly pink is the silent omission
    # this whole record exists to prevent. The full state, and where a refused link actually
    # pointed, ride the tooltip.
    ctx_chips = "".join(
        '<span class="ctxchip {cls}" title="{title}">{file}{label}</span>'.format(
            cls=esc(c["state"].split()[0]),
            title=esc(c["state"] + (f" -> {c['resolves_to']}" if c.get("resolves_to") else "")),
            file=esc(c["file"]),
            label="" if c["state"] == "read" else f" &middot; {esc(c['state'].split()[0])}",
        )
        for c in read
    )
    ctx_html = (
        f'<div class="ctxread"><span class="dim">The team was given:</span> {ctx_chips}</div>'
        if read
        else '<p class="dim">No engagement context was supplied. Drop notes into '
        "<code>context/</code> and the team reads them on the next run.</p>"
    )
    return (
        f'{gate}<div class="tiles">{tiles}</div>'
        f'<div class="rec"><div class="lbl">Our recommendation</div><p>{mdlite(rec)}</p></div>'
        '<div class="grid2">'
        + _card(
            "How hard we pushed on each other",
            _bar(sev)
            + f'<p class="dim">{accepted} of {len(pushbacks)} challenges changed the work.</p>',
        )
        + _card("Challenges accepted", _donut(accepted, len(pushbacks), "of challenges taken"))
        + "</div>"
        + f"<h3>What the team was working from</h3>{ctx_html}"
    )


def _needs_you(escalations, manifest) -> str:
    if not escalations:
        return '<p class="dim">Nothing was escalated. Read the plan and decide.</p>'
    cards = "".join(
        _card(f"Question {i}", f"<p>{mdlite(q)}</p>", tone="warn")
        for i, q in enumerate(escalations, 1)
    )
    notes = manifest.get("annotations") or []
    notes_html = ""
    if notes:
        items = "".join(f"<li><b>{esc(n['by'])}</b>: {mdlite(n['note'])}</li>" for n in notes)
        notes_html = f'<h3>Your notes so far</h3><ul class="plain">{items}</ul>'
    return (
        "<p>These came from the Engagement Lead. It says only a human can answer them, and the "
        "gate holds the run until you do.</p>"
        f'<div class="grid2">{cards}</div>{notes_html}'
    )


def _team(plan) -> str:
    dispatched, absent = staffing(plan)
    rows = "".join(
        f'<tr><td class="k">{esc(d["title"])}</td><td>{esc(d["why"])}</td></tr>' for d in dispatched
    )
    return (
        "<h3>On this run</h3>"
        f"{_people(dispatched, absent)}"
        f"<h3>Why each was called in</h3><table>{rows}</table>"
    )


def _debate(pushbacks, regs) -> str:
    if not pushbacks:
        return '<p class="dim">No challenges were recorded.</p>'
    rows = "".join(
        f'<details class="pbrow {"kept" if p["disposition"] == "accepted" else "held"}">'
        f'<summary><span class="who">{esc(p["role_label"])}</span>'
        f'<span class="sev {esc(p["severity"])}">{esc(p["severity"])}</span>'
        f'<span class="dim2">{esc(p["dimension"])}</span>'
        f'<span class="disp">{esc(p["disposition"])}</span></summary>'
        f'<p class="claim">{mdlite(p["claim"])}</p>'
        f'<p class="resp">{mdlite(p["response"] or "No response recorded.")}</p></details>'
        for p in pushbacks
    )
    dis = regs.get("disagreements") or []
    dis_html = ""
    if dis:
        items = "".join(f"<li>{mdlite(d)}</li>" for d in dis)
        dis_html = f"<h3>Unresolved between advisors</h3><ul class='plain'>{items}</ul>"
    return f"<h3>Every challenge and what it changed</h3>{rows}{dis_html}"


def _plan_tab(lead_sections, regs) -> str:
    body = lead_sections.get("body", "")
    parts = []
    for name in ("decisions", "disagreements", "escalations"):
        entries = regs.get(name) or []
        if entries:
            items = "".join(f"<li>{mdlite(e)}</li>" for e in entries)
            parts.append(f"<h3>{name.title()}</h3><ul class='plain'>{items}</ul>")
    milestones = parse_milestones(body)
    if milestones:
        parts.append(f"<h3>Milestones</h3>{_timeline(milestones)}")
    risks = lead_sections.get("risks")
    if risks:
        parts.append(f"<h3>What could go wrong</h3><p>{mdlite(risks)}</p>")
    return "".join(parts) or '<p class="dim">The Engagement Lead produced no plan.</p>'


def _actions(lead_sections) -> str:
    steps = _steps(lead_sections.get("next steps", ""))
    if not steps:
        return '<p class="dim">No next steps were produced.</p>'
    mine = [s for s in steps if not _is_client_step(s)]
    theirs = [s for s in steps if _is_client_step(s)]

    def block(title, items, note):
        if not items:
            return _card(title, f'<p class="dim">{esc(note)}</p>')
        lis = "".join(f'<li><label><input type="checkbox"> {mdlite(s)}</label></li>' for s in items)
        return _card(title, f"<ul class='check'>{lis}</ul>")

    return (
        "<p>Split by who moves. This is a keyword split for now, so check it &mdash; the "
        "Engagement Lead will label them itself in a later version.</p>"
        '<div class="grid2">'
        + block("Yours to do", mine, "Nothing landed on you.")
        + block("With the client", theirs, "Nothing needs the client yet.")
        + "</div>"
    )


def _docs(manifest, run_dir: Path) -> str:
    files = sorted(p.name for p in run_dir.glob("*.md"))
    rows = "".join(
        f'<tr><td class="k">{esc(f)}</td><td class="dim">source artifact</td></tr>' for f in files
    )
    return (
        "<h3>Produced this run</h3>"
        f"<table>{rows}</table>"
        "<h3>Draftable deliverables</h3>"
        '<p class="dim">Nothing yet. SOW and RFQ drafting is the next build: templates in '
        "<code>references/</code>, a drafting step after synthesis, and routing that recognises "
        "a proposal request. This tab will list them here with a download link.</p>"
    )


def render_dashboard(manifest: dict, run_dir: Path) -> str:
    # The same status guard and the same artifact verification `render_run` passes. This is a
    # different view of a run, not a lower bar for showing one.
    precheck(manifest, run_dir)
    status = manifest.get("status")
    artifacts = manifest.get("artifacts") or []
    plan = manifest.get("plan") or {}
    lead = next((a for a in artifacts if a["role"] == SYNTHESIS_ROLE and not a.get("error")), None)
    lead_text = (
        (run_dir / lead["file"]).read_text(encoding="utf-8") if lead and lead.get("file") else ""
    )
    lead_sections = split_sections(lead_text) if lead_text else {}
    regs = parse_registers(lead_sections.get("body", "")) if lead_sections else {}
    pushbacks = pushback_rows(artifacts, by_severity=True)  # a scan, so worst first
    escalations = _escalations(artifacts)
    headline, context = split_headline(manifest.get("task", ""))

    panes = {
        "overview": _overview(manifest, lead_sections, regs, artifacts, pushbacks, escalations),
        "needs-you": _needs_you(escalations, manifest),
        "team": _team(plan),
        "debate": _debate(pushbacks, regs),
        "plan": _plan_tab(lead_sections, regs),
        "actions": _actions(lead_sections),
        "docs": _docs(manifest, run_dir),
    }
    nav = "".join(
        f'<button class="tab{" on" if i == 0 else ""}" data-t="{tid}">{esc(label)}'
        + (
            f'<span class="badge">{len(escalations)}</span>'
            if tid == "needs-you" and escalations
            else ""
        )
        + "</button>"
        for i, (tid, label) in enumerate(TABS)
    )
    body = "".join(
        f'<section class="pane{" on" if i == 0 else ""}" id="p-{tid}">{panes[tid]}</section>'
        for i, (tid, _) in enumerate(TABS)
    )
    return _PAGE.format(
        title=esc(headline or manifest.get("run_id", "")),
        context=esc(context),
        run=esc(manifest.get("run_id", "")),
        status=esc(status),
        nav=nav,
        body=body,
        css=_CSS,
    )


_CSS = """
*{box-sizing:border-box}
:root{--bg:#f4f4f8;--panel:#fff;--ink:#1a1a2e;--ink2:#3d3d5c;--ink3:#6f6f8f;--line:#e4e4ef;
--accent:#7a78f5;--warn:#c0453c;--ok:#2f7d5d;--sans:"DM Sans",Inter,system-ui,sans-serif;
--body:Inter,system-ui,-apple-system,sans-serif}
html[data-theme=dark]{--bg:#0e0e1c;--panel:#17172b;--ink:#f2f2f8;--ink2:#c9c9dd;--ink3:#9494b4;
--line:#2a2a44}
body{margin:0;background:var(--bg);color:var(--ink2);font:15px/1.6 var(--body)}
header{background:var(--panel);border-bottom:1px solid var(--line);padding:18px 24px 0}
.hd{display:flex;align-items:flex-start;gap:16px;max-width:1180px;margin:0 auto}
.hd h1{font:700 21px/1.3 var(--sans);color:var(--ink);margin:0 0 4px;flex:1 1 auto}
.hd .meta{font-size:12px;color:var(--ink3);text-align:right;flex:0 0 auto}
.chip{display:inline-block;padding:2px 9px;border-radius:99px;font-size:11px;font-weight:600;
letter-spacing:.04em;text-transform:uppercase;background:#eeeef8;color:var(--ink3)}
.chip.pending{background:#fdf0e6;color:#a8631f}
.ctx{max-width:1180px;margin:0 auto;font-size:13px;color:var(--ink3);padding-bottom:12px}
nav{max-width:1180px;margin:0 auto;display:flex;gap:2px;overflow-x:auto}
.tab{appearance:none;border:0;background:transparent;font:600 13px/1 var(--sans);
color:var(--ink3);padding:12px 14px;cursor:pointer;border-bottom:2px solid transparent;
white-space:nowrap}
.tab:hover{color:var(--ink)}
.tab.on{color:var(--accent);border-bottom-color:var(--accent)}
.badge{display:inline-block;margin-left:6px;background:var(--warn);color:#fff;border-radius:99px;
padding:1px 6px;font-size:10px}
main{max-width:1180px;margin:0 auto;padding:22px 24px 60px}
.pane{display:none}.pane.on{display:block}
h3{font:600 12px/1.3 var(--sans);letter-spacing:.07em;text-transform:uppercase;color:var(--ink3);
margin:22px 0 10px}
h3:first-child{margin-top:0}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:10px;
margin:0 0 16px}
.tile{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:12px 14px}
.tile-v{display:block;font:700 26px/1.1 var(--sans);color:var(--ink)}
.tile-l{display:block;font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:var(--ink3);
margin-top:4px}
.tile.warn .tile-v{color:var(--warn)}
.banner{border-radius:10px;padding:12px 16px;margin:0 0 16px;font-size:14px}
.banner.warn{background:#fdeceb;border:1px solid #f2cbc7;color:#8f342d}
.banner.ok{background:#eaf6f0;border:1px solid #c6e5d6;color:#256b4e}
html[data-theme=dark] .banner.warn{background:#2c1a1c;border-color:#5b2f2f;color:#ff9c92}
html[data-theme=dark] .banner.ok{background:#152a22;border-color:#2c5343;color:#7fd4ac}
.rec{background:var(--panel);border:1px solid var(--line);border-left:3px solid var(--accent);
border-radius:10px;padding:14px 18px;margin:0 0 16px}
.rec .lbl{font:600 11px/1 var(--sans);letter-spacing:.07em;text-transform:uppercase;
color:var(--ink3);margin-bottom:6px}
.rec p{margin:0;font-size:16px;color:var(--ink)}
.grid2{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:12px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:14px 16px}
.card.warn{border-left:3px solid var(--warn)}
.card h4{font:600 13px/1.3 var(--sans);color:var(--ink);margin:0 0 8px}
.card-body p{margin:0 0 8px}.card-body p:last-child{margin:0}
table{width:100%;border-collapse:collapse;background:var(--panel);border:1px solid var(--line);
border-radius:10px;overflow:hidden;font-size:14px}
td{padding:9px 14px;border-bottom:1px solid var(--line);vertical-align:top}
tr:last-child td{border-bottom:none}
td.k{font-weight:600;color:var(--ink);width:15rem}
table.muted td{font-size:13px}
.dim{color:var(--ink3);font-size:13px}
ul.plain{margin:0;padding-left:18px}ul.plain li{margin:6px 0}
ul.check{list-style:none;margin:0;padding:0}
ul.check li{margin:6px 0;background:var(--panel);border:1px solid var(--line);border-radius:8px;
padding:9px 12px}
ul.check label{display:flex;gap:10px;align-items:flex-start;cursor:pointer}
.pbrow{background:var(--panel);border:1px solid var(--line);border-left:3px solid var(--line);
border-radius:8px;margin:6px 0;padding:9px 13px}
.pbrow.kept{border-left-color:var(--accent)}.pbrow.held{border-left-color:var(--warn)}
.pbrow summary{cursor:pointer;display:flex;gap:10px;align-items:baseline;flex-wrap:wrap;
font-size:13px;list-style:none}
.pbrow summary::-webkit-details-marker{display:none}
.who{font-weight:600;color:var(--ink);min-width:11rem}
.sev{font-size:10px;letter-spacing:.05em;text-transform:uppercase;
padding:1px 7px;border-radius:99px;background:#eeeef8;color:var(--ink3)}
.sev.blocking{background:#fdeceb;color:var(--warn)}
.sev.serious{background:#fdf3e6;color:#a8631f}
.dim2{font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:var(--ink3)}
.disp{margin-left:auto;font-size:11px;text-transform:uppercase;letter-spacing:.05em;font-weight:600;
color:var(--ink3)}
.pbrow.kept .disp{color:var(--accent)}
.claim{margin:9px 0 6px;font-size:14px;color:var(--ink2)}
.resp{margin:0;font-size:13px;color:var(--ink3);padding-left:12px;border-left:2px solid var(--line)}
.tgl{appearance:none;border:1px solid var(--line);background:var(--panel);color:var(--ink3);
border-radius:6px;font:500 12px var(--body);padding:5px 10px;cursor:pointer;margin-left:12px}
code{background:#eeeef8;padding:1px 5px;border-radius:4px;font-size:.88em}

/* --- visuals: shapes you read at a glance --- */
.bar{display:flex;height:14px;border-radius:99px;overflow:hidden;
background:var(--line);margin:6px 0}
.seg{display:block;height:100%}
.s-block{background:var(--warn)}.s-serious{background:#e0913c}.s-minor{background:var(--accent)}
.keys{display:flex;gap:14px;flex-wrap:wrap;font-size:12px;color:var(--ink3);margin-bottom:8px}
.key i{display:inline-block;width:9px;height:9px;border-radius:2px;margin-right:5px}
.key i.s-block{background:var(--warn)}.key i.s-serious{background:#e0913c}
.key i.s-minor{background:var(--accent)}
.donut{display:flex;align-items:center;gap:14px}
.ring-bg{fill:none;stroke:var(--line);stroke-width:9}
.ring-fg{fill:none;stroke:var(--accent);stroke-width:9;stroke-linecap:round}
.ring-t{font:700 19px var(--sans);fill:var(--ink);text-anchor:middle}
.donut-l{font-size:13px;color:var(--ink3)}
.people{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 6px}
.person{display:flex;align-items:center;gap:8px;background:var(--panel);
border:1px solid var(--line);
border-radius:99px;padding:5px 12px 5px 5px;font-size:13px}
.person.on{border-color:var(--accent)}
.person.off{opacity:.62}
.av{display:grid;place-items:center;width:26px;height:26px;border-radius:99px;
background:var(--line);color:var(--ink3);font:600 10px var(--sans)}
.person.on .av{background:var(--accent);color:#fff}
.pn{color:var(--ink);font-weight:500}
.people.bench .pn{font-weight:400;color:var(--ink3)}
.timeline{list-style:none;margin:0;padding:0}
.timeline li{display:flex;gap:12px;padding:0 0 14px 0;position:relative}
.timeline li:not(:last-child)::before{content:"";position:absolute;left:13px;top:28px;bottom:0;
width:2px;background:var(--line)}
.timeline .dot{flex:0 0 auto;display:grid;place-items:center;width:28px;height:28px;
border-radius:99px;background:var(--accent);color:#fff;font:600 12px var(--sans);z-index:1}
.timeline li>div{padding-top:4px;font-size:14px}
.ctxread{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
/* The base chip reads as "we read this". Every state that did NOT contribute its bytes has
   to look different from it, or a file the run refused renders exactly like one it used. */
.ctxchip{background:#eaf6f0;color:#256b4e;border-radius:99px;padding:3px 11px;font-size:12px}
.ctxchip.truncated{background:#fdf3e6;color:#a8631f}
.ctxchip.dropped{background:#fdeceb;color:var(--warn)}
.ctxchip.empty{background:#eeeef3;color:var(--ink3)}
.ctxchip.unreadable{background:#fdeceb;color:var(--warn)}
.ctxchip.refused{background:#fdeceb;color:var(--warn);font-weight:600;text-decoration:underline}
.ctxchip.unresolvable{background:#fdeceb;color:var(--warn)}

html[data-theme=dark] code{background:#22223c}
"""

_PAGE = """<!doctype html><html data-theme="light"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@500;600;700&family=Inter:wght@400;500;600&display=swap">
<style>{css}</style></head><body>
<header>
  <div class="hd">
    <div style="flex:1 1 auto">
      <h1>{title}</h1>
      <div class="ctx">{context}</div>
    </div>
    <div class="meta"><span class="chip {status}">{status}</span><br>{run}
      <button class="tgl" id="tgl" type="button">Dark</button></div>
  </div>
  <nav>{nav}</nav>
</header>
<main>{body}</main>
<script>
document.querySelectorAll('.tab').forEach(function(b){{
  b.addEventListener('click',function(){{
    document.querySelectorAll('.tab').forEach(function(x){{x.classList.remove('on')}});
    document.querySelectorAll('.pane').forEach(function(x){{x.classList.remove('on')}});
    b.classList.add('on');
    document.getElementById('p-'+b.dataset.t).classList.add('on');
    location.hash = b.dataset.t;
  }});
}});
if (location.hash) {{
  var t = document.querySelector('.tab[data-t="'+location.hash.slice(1)+'"]');
  if (t) t.click();
}}
document.getElementById('tgl').addEventListener('click',function(){{
  var r=document.documentElement;
  var n=r.getAttribute('data-theme')==='dark'?'light':'dark';
  r.setAttribute('data-theme',n); this.textContent=n==='dark'?'Light':'Dark';
}});
</script>
</body></html>"""
