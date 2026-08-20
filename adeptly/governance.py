import re
from dataclasses import dataclass, field

REQUIRED_SECTIONS: tuple[str, ...] = ("objective", "citations", "risks", "next steps")
PLACEHOLDER_RE = re.compile(r"^\s*(\.\.\.|tbd|todo|n/a|lorem ipsum)?\s*$", re.IGNORECASE)
URL_RE = re.compile(r"https?://\S+")
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b")


@dataclass
class Review:
    ok: bool
    issues: list[str] = field(default_factory=list)

    @property
    def verdict(self) -> str:
        return "APPROVE" if self.ok else "REVISE"


def _section_body(text: str, section: str) -> str | None:
    """Return the text following 'Section:' up to the next 'Word:' line, or None if absent."""
    m = re.search(rf"(?im)^[ \t]*{re.escape(section)}[ \t]*:[ \t]*(.*)$", text)
    if not m:
        return None
    start = m.end(1)
    tail = text[start:]
    nxt = re.search(r"(?m)^\s*[A-Za-z][A-Za-z /&]{1,30}:", tail)
    rest = tail[: nxt.start()] if nxt else tail
    return (m.group(1) + rest).strip()


def review_text(text: str) -> Review:
    """Rule-based pre-release check. Cheap, deterministic, and the same for every role."""
    issues: list[str] = []
    for sec in REQUIRED_SECTIONS:
        body = _section_body(text, sec)
        if body is None:
            issues.append(f"Missing section: {sec}")
        elif PLACEHOLDER_RE.match(body):
            issues.append(f"Placeholder content in section: {sec}")
    if not URL_RE.search(text):
        issues.append("Missing citation URL(s)")
    if EMAIL_RE.search(text):
        issues.append("Possible PII: email address present")
    if PHONE_RE.search(text):
        issues.append("Possible PII: phone number present")
    return Review(ok=not issues, issues=issues)
