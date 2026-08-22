import re
from dataclasses import dataclass, field

# Every deliverable must carry these, in any order. Headings may be plain ("Risks:"),
# markdown ("## Risks", "**Risks:**") or list items ("- Risks:"); matching is case-insensitive.
REQUIRED_SECTIONS: tuple[str, ...] = ("objective", "body", "citations", "risks", "next steps")
MIN_SECTION_CHARS = 3

# Accept the common label variants: "Objective(s)", "Next Step(s)".
_SECTION_ALT = "|".join(re.escape(sec.rstrip("s")) + "s?" for sec in REQUIRED_SECTIONS)
# A heading is a section name at line start. Markdown headings ('## Risks', '## 2. Risks') need
# no colon. A bold label ('**Risks**') counts when it is alone on its line or has a colon, so
# prose like '**Risks** of delay are real' stays body text. A plain word, a list item ('- Risks:')
# or a numbered line ('2. Risks:') counts only with a colon.
_HEADING_RE = re.compile(
    rf"^[ \t]*(?P<hash>#+[ \t]*(?:\d+[.)][ \t]*)?)?(?:[-*][ \t]+|\d+[.)][ \t]+)?"
    rf"(?P<bold>\*\*)?(?P<name>{_SECTION_ALT})(?:\*\*)?[ \t]*(?P<colon>:)?(?:\*\*)?"
    rf"[ \t]*(?P<rest>.*)$",
    re.IGNORECASE | re.MULTILINE,
)
PLACEHOLDER_RE = re.compile(
    r"^\s*(?:\.{2,}|[-–—.]+\s*$|tbd\b|todo\b|n/?a\b|lorem ipsum|to be (?:determined|completed))",
    re.IGNORECASE,
)
HTTPS_RE = re.compile(r"https://\S+")
# Model output is printed to a terminal at review time. ANSI/OSC sequences could repaint the
# screen just before a human types "approve", so they are a governance failure, not cosmetics.
CONTROL_RE = re.compile(r"[\x00-\x08\x0b-\x1f\x7f-\x9f]")
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
# Phone needs separators or parentheses so a bare 10-digit figure (a population, a budget) is
# not flagged; card-shaped numbers must also pass a Luhn check so four years in a row are not.
PHONE_RE = re.compile(
    r"(?<!\d)(?:\+?1[-.\s]?)?(?:\(\d{3}\)[-.\s]?|\d{3}[-.\s])\d{3}[-.\s]\d{4}(?!\d)"
)
SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
CARD_RE = re.compile(r"\b\d{4}[ -]?\d{4}[ -]?\d{4}[ -]?\d{4}\b")


def strip_controls(text: str) -> str:
    """Make model output safe to print: keep newlines and tabs, drop every other control byte."""
    return CONTROL_RE.sub("", text)


def flagged_roles(artifacts: list[dict]) -> list[str]:
    """Roles whose artifact is not clean, by content or by what happened while producing it.

    `review` is derived purely from the artifact bytes, so the gate can re-derive and verify it.
    `process_flags` records what the bytes cannot show — a truncated generation, a blocking
    critique the author dismissed — and counts just as much toward needing a human's --force.
    """
    return [
        a["role"]
        for a in artifacts
        if a.get("error") or not (a.get("review") or {}).get("ok") or a.get("process_flags")
    ]


@dataclass
class Review:
    ok: bool
    issues: list[str] = field(default_factory=list)

    @property
    def verdict(self) -> str:
        return "APPROVE" if self.ok else "REVISE"


def _luhn_ok(digits: str) -> bool:
    ds = [int(c) for c in digits if c.isdigit()]
    total = 0
    for i, d in enumerate(reversed(ds)):
        if i % 2 == 1:
            d = d * 2 - 9 if d * 2 > 9 else d * 2
        total += d
    return total % 10 == 0


_CANONICAL = {sec.rstrip("s"): sec for sec in REQUIRED_SECTIONS}


def _canonical(label: str) -> str:
    return _CANONICAL[label.lower().rstrip("s")]


def split_sections(text: str) -> dict[str, str]:
    """Map each recognised heading (lower-case) to the text under it, up to the next heading."""
    found: dict[str, str] = {}
    matches = [
        m
        for m in _HEADING_RE.finditer(text)
        if m.group("hash") or m.group("colon") or (m.group("bold") and not m.group("rest"))
    ]
    for i, m in enumerate(matches):
        name = _canonical(m.group("name"))
        if name in found:
            continue
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        found[name] = (m.group("rest") + text[m.end() : end]).strip()
    return found


def review_text(text: str) -> Review:
    """Rule-based pre-release check. Cheap, deterministic, the same for every role."""
    issues: list[str] = []
    sections = split_sections(text)
    for sec in REQUIRED_SECTIONS:
        body = sections.get(sec)
        if body is None:
            issues.append(f"Missing section: {sec}")
        elif not body or PLACEHOLDER_RE.match(body):
            issues.append(f"Placeholder content in section: {sec}")
        elif len(body) < MIN_SECTION_CHARS:
            issues.append(f"Section too short: {sec}")
    citations = sections.get("citations", "")
    if citations and not HTTPS_RE.search(citations):
        issues.append("Missing https citation URL in Citations section")
    if CONTROL_RE.search(text):
        issues.append("Control characters present (terminal escape risk)")
    if EMAIL_RE.search(text):
        issues.append("Possible PII: email address present")
    if PHONE_RE.search(text):
        issues.append("Possible PII: phone number present")
    if SSN_RE.search(text):
        issues.append("Possible PII: SSN-shaped number present")
    if any(_luhn_ok(m.group(0)) for m in CARD_RE.finditer(text)):
        issues.append("Possible PII: card-shaped number present")
    return Review(ok=not issues, issues=issues)
