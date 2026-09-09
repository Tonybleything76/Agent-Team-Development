"""Read the run log and report the team's patterns back to you.

The point is not a dashboard. It is that a few of these numbers are only meaningful as warnings:
a critique loop where the author accepts every single point is not obviously working, it is
plausibly just agreeable in the other direction. Surfacing that is how the team gets better
over time rather than merely feeling better.
"""

import json
from collections import Counter
from pathlib import Path

# Below this many critique points, an acceptance rate is noise rather than a signal.
MIN_POINTS_FOR_SIGNAL = 10


def read_events(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    events = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue  # a spliced line is a lost record, not a reason to fail the report
    return events


def summarize(events: list[dict]) -> dict:
    by_event = Counter(e.get("event") for e in events)
    critiques = [e for e in events if e.get("event") == "critique"]
    points = sum(c.get("points", 0) for c in critiques)
    accepted = sum(c.get("accepted", 0) for c in critiques)
    decisions = [e for e in events if e.get("event") in ("approved", "rejected")]
    forced = sum(1 for e in decisions if e.get("forced"))
    return {
        "runs_started": by_event.get("run_start", 0),
        "runs_completed": by_event.get("run_end", 0),
        "specialist_errors": by_event.get("specialist_error", 0),
        "critiques": len(critiques),
        "critique_points": points,
        "critique_points_accepted": accepted,
        "critique_acceptance_rate": (accepted / points) if points else None,
        "unresolved_blocking": sum(c.get("unresolved_blocking", 0) for c in critiques),
        "artifacts_revised": sum(1 for c in critiques if c.get("revised")),
        "approved": by_event.get("approved", 0),
        "rejected": by_event.get("rejected", 0),
        "forced_approvals": forced,
        "annotations": by_event.get("annotated", 0),
        "reopened": by_event.get("reopened", 0),
    }


def warnings(summary: dict) -> list[str]:
    """The readings worth acting on. Silence here means nothing looks off, not that all is well."""
    out = []
    rate, points = summary["critique_acceptance_rate"], summary["critique_points"]
    if rate is not None and points >= MIN_POINTS_FOR_SIGNAL:
        if rate == 1.0:
            out.append(
                f"Authors accepted all {points} critique points. A critic is only doing half its "
                "job if nobody ever pushes back; check whether the critiques are good or the "
                "authors are simply deferring."
            )
        elif rate < 0.2:
            out.append(
                f"Authors accepted only {rate:.0%} of {points} critique points. Either the critic "
                "is off target or the authors are dismissing it; read a few rejections."
            )
    if summary["critiques"] == 0 and summary["runs_completed"]:
        out.append("No critiques recorded. Runs may be going through with --no-critique.")
    if summary["forced_approvals"]:
        out.append(
            f"{summary['forced_approvals']} approval(s) overrode a governance flag with --force. "
            "Those carry a written reason; they are worth re-reading periodically."
        )
    if summary["reopened"]:
        out.append(
            f"{summary['reopened']} decision(s) were reopened. That is the system working, not "
            "failing: changing your mind stayed cheap."
        )
    return out
