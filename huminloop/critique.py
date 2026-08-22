"""Structured critique and response.

The patterns here are the ones with the best evidence behind them, assembled so that critique
changes the artifact rather than decorating it:

- **Steelman first.** The critic must state the strongest version of the work before attacking
  it. Critique of a strawman is noise, and forcing the steelman is what stops it.
- **Named dimensions.** "What do you think" produces agreeable mush. A fixed rubric produces
  findings that can be argued with.
- **Pre-mortem.** Assume it failed twelve months out and explain why. Prospective hindsight
  surfaces failure modes that "any risks?" does not.
- **Critique does not revise.** The critic never edits the artifact. The author answers every
  point and owns the change, which keeps authorship and accountability together.
- **Dismissal is allowed but recorded.** A specialist may reject a critique with a reason. An
  unresolved blocking critique makes the run governance-flagged, so releasing it anyway needs a
  named human, --force and a written note. Suppressing dissent is possible and never silent.
"""

import re
from dataclasses import asdict, dataclass, field

DIMENSIONS = ("evidence", "feasibility", "human-impact", "consistency", "falsifiability")
SEVERITIES = ("blocking", "serious", "minor")

CRITIC_INSTRUCTIONS = f"""You are reviewing a teammate's draft deliverable. Your job is to make
it stronger, not to be agreeable and not to be harsh for its own sake. A critique that could
apply to any document is worthless; cite the specific claim you are challenging.

Answer in exactly this format, with no other text:

STEELMAN: one paragraph stating the strongest version of this work's argument, in your own
words. If you cannot state it fairly, you have not understood it well enough to critique it.

PREMORTEM: it is twelve months later and following this deliverable led to a bad outcome.
In one paragraph, say what went wrong and which part of the draft caused it.

Then one line per finding, at most six, strongest first:
POINT: <severity> | <dimension> | <the specific claim you challenge, and what would make it
sound>

severity is one of: {", ".join(SEVERITIES)}. Use "blocking" only for something that makes the
deliverable wrong or unsafe to act on, not merely improvable.
dimension is one of: {", ".join(DIMENSIONS)}.

If the work is sound, say so: emit STEELMAN, PREMORTEM, and a single line
POINT: minor | consistency | No substantive challenge; I checked <what you checked> and it holds.
Do not manufacture disagreement to fill the section."""

AUTHOR_INSTRUCTIONS = """A reviewer has challenged your draft. Answer every point, then reissue
the deliverable.

For each numbered point, one line, in order:
RESPONSE <n>: ACCEPTED | REJECTED — <what you changed, or why the challenge does not hold>

Reject only when you have a reason you would defend out loud; "I disagree" is not a reason.
Accepting means the reissued deliverable actually reflects the change.

Then:
REVISED:
<the complete deliverable, all sections, incorporating everything you accepted>"""


@dataclass
class CritiquePoint:
    severity: str
    dimension: str
    claim: str
    disposition: str | None = None  # accepted | rejected, set by the author's response
    response: str = ""

    @property
    def unresolved(self) -> bool:
        return self.disposition != "accepted"


@dataclass
class Critique:
    critic_role: str
    steelman: str = ""
    premortem: str = ""
    points: list[CritiquePoint] = field(default_factory=list)

    @property
    def blocking_unresolved(self) -> list[CritiquePoint]:
        return [p for p in self.points if p.severity == "blocking" and p.unresolved]

    def as_dict(self) -> dict:
        return asdict(self)


_POINT_RE = re.compile(r"^\s*POINT\s*:\s*(.+)$", re.IGNORECASE | re.MULTILINE)
_FIELD_RE = r"^\s*{name}\s*:\s*(.*?)(?=^\s*(?:STEELMAN|PREMORTEM|POINT|RESPONSE|REVISED)\s*:|\Z)"
_RESPONSE_RE = re.compile(
    r"^\s*RESPONSE\s*(\d+)\s*:\s*(ACCEPTED|REJECTED)\s*[-—:]*\s*(.*)$",
    re.IGNORECASE | re.MULTILINE,
)


def _field(text: str, name: str) -> str:
    m = re.search(_FIELD_RE.format(name=name), text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
    return m.group(1).strip() if m else ""


def parse_critique(text: str, critic_role: str) -> Critique:
    """Tolerant parse: a critic that drifts from the format still yields its findings."""
    critique = Critique(
        critic_role=critic_role,
        steelman=_field(text, "STEELMAN"),
        premortem=_field(text, "PREMORTEM"),
    )
    for raw in _POINT_RE.findall(text):
        parts = [p.strip() for p in raw.split("|", 2)]
        severity = parts[0].lower() if parts and parts[0].lower() in SEVERITIES else "serious"
        dimension = (
            parts[1].lower() if len(parts) > 1 and parts[1].lower() in DIMENSIONS else "consistency"
        )
        claim = parts[2] if len(parts) > 2 else raw.strip()
        if claim:
            critique.points.append(CritiquePoint(severity, dimension, claim))
    return critique


def apply_responses(critique: Critique, text: str) -> None:
    """Attach the author's disposition to each point. Unanswered points stay unresolved."""
    for index, disposition, reason in _RESPONSE_RE.findall(text):
        i = int(index) - 1
        if 0 <= i < len(critique.points):
            critique.points[i].disposition = disposition.lower()
            critique.points[i].response = reason.strip()


def extract_revision(text: str) -> str | None:
    m = re.search(r"^\s*REVISED\s*:\s*$(.*)", text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
    if not m:
        m = re.search(r"^\s*REVISED\s*:\s*(.+)", text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
    body = m.group(1).strip() if m else ""
    return body or None


def numbered_points(critique: Critique) -> str:
    return "\n".join(
        f"{i + 1}. [{p.severity}/{p.dimension}] {p.claim}" for i, p in enumerate(critique.points)
    )
