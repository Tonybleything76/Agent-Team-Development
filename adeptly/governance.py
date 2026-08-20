import re
from dataclasses import dataclass, field

# Every deliverable must carry these, in any order. Headings may be plain ("Risks:"),
# markdown ("## Risks", "**Risks:**") or list items ("- Risks:"); matching is case-insensitive.
REQUIRED_SECTIONS: tuple[str, ...] = ("objective", "body", "citations", "risks", "next steps")
MIN_SECTION_CHARS = 3

_SECTION_ALT = "|".join(re.escape(s) for s in REQUIRED_SECTIONS)
# A heading is a section name at line start, either followed by ':' or wrapped in a markdown
# marker ('## Risks', '**Risks**', '- Risks'). A bare word with neither is body text.
_HEADING_RE = re.compile(
    rf"^[ \t]*(?P<md>#+[ \t]*|[-*][ \t]+|\*\*)?(?P<name>{_SECTION_ALT})(?:\*\*)?[ \t]*"
    rf"(?P<colon>:)?(?:\*\*)?[ \t]*(?P<rest>.*)$",
    re.IGNORECASE | re.MULTILINE,
)
PLACEHOLDER_RE = re.compile(
    r"^\s*(?:\.{2,}|[-–—.]+\s*$|tbd\b|todo\b|n/?a\b|lorem ipsum|to be (?:determined|completed))",
    re.IGNORECASE,
)
HTTPS_RE = re.compile(r"https://\S+")
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?<!\d)(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}(?!\d)")
SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
CARD_RE = re.compile(r"\b\d{4}[ -]?\d{4}[ -]?\d{4}[ -]?\d{4}\b")


@dataclass
class Review:
    ok: bool
    issues: list[str] = field(default_factory=list)

    @property
    def verdict(self) -> str:
        return "APPROVE" if self.ok else "REVISE"


def split_sections(text: str) -> dict[str, str]:
    """Map each recognised heading (lower-case) to the text under it, up to the next heading."""
    found: dict[str, str] = {}
    matches = [m for m in _HEADING_RE.finditer(text) if m.group("md") or m.group("colon")]
    for i, m in enumerate(matches):
        name = m.group("name").lower()
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
    if EMAIL_RE.search(text):
        issues.append("Possible PII: email address present")
    if PHONE_RE.search(text):
        issues.append("Possible PII: phone number present")
    if SSN_RE.search(text):
        issues.append("Possible PII: SSN-shaped number present")
    if CARD_RE.search(text):
        issues.append("Possible PII: card-shaped number present")
    return Review(ok=not issues, issues=issues)
