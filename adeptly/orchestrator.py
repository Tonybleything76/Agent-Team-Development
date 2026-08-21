import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path

from . import __version__
from .gate import flagged_roles
from .governance import Review, review_text
from .llm import LLMClient, build_prompt, get_llm
from .roles import SPECIALISTS, get_role
from .router import Plan, Router
from .storage import (
    append_log,
    artifact_root,
    clear_lock,
    new_run_id,
    now_iso,
    run_dir,
    write_lock,
    write_manifest,
)

log = logging.getLogger(__name__)
# Each specialist sees at most this many characters of every predecessor's artifact.
CONTEXT_CHARS = 600


@dataclass
class ArtifactRecord:
    role: str
    file: str | None
    review: dict | None
    error: str | None = None


@dataclass
class RunRecord:
    run_id: str
    task: str
    provider: str
    plan: dict
    artifacts: list[ArtifactRecord] = field(default_factory=list)
    status: str = "running"
    created_at: str = ""
    version: str = __version__

    @property
    def all_approved_by_governance(self) -> bool:
        return not flagged_roles([asdict(a) for a in self.artifacts])


def _excerpt(text: str) -> str:
    return text if len(text) <= CONTEXT_CHARS else text[:CONTEXT_CHARS] + " …"


def produce(role_key: str, task: str, llm: LLMClient, context: str = "") -> tuple[str, Review]:
    role = get_role(role_key)
    if role_key not in SPECIALISTS:
        raise ValueError(f"'{role_key}' is a supervisor role and cannot be dispatched")
    system, prompt = build_prompt(role, task, context)
    text = llm.generate(system, prompt, role=role_key)
    return text, review_text(text)


def run(
    task: str,
    *,
    llm: LLMClient | None = None,
    router: Router | None = None,
    root: Path | None = None,
    log_file: Path | None = None,
) -> RunRecord:
    """Route a task, run specialists in order, governance-check each artifact, park in pending/.

    The manifest is written before the first specialist runs and after every artifact, so an
    interrupted run is still visible (status 'running') and can be rejected by a human.
    """
    if not task or not task.strip():
        raise ValueError("task must be a non-empty string")
    llm = llm or get_llm()
    router = router or Router()
    plan: Plan = router.route(task)
    run_id = new_run_id()
    record = RunRecord(
        run_id=run_id,
        task=task,
        provider=llm.name,
        plan={"roles": plan.roles, "matched_rules": plan.matched_rules},
        created_at=now_iso(),
    )
    out = run_dir(artifact_root(root), "pending", run_id)
    out.mkdir(parents=True, exist_ok=False)  # a collision is a bug, never a silent merge
    write_lock(out)  # tells the gate a live process owns this directory
    write_manifest(out, asdict(record))
    append_log(
        {
            "event": "run_start",
            "run_id": run_id,
            "task": task,
            "roles": plan.roles,
            "provider": llm.name,
        },
        log_file,
    )
    log.info("run %s: %d specialist(s) %s", run_id, len(plan.roles), plan.roles)

    context_parts: list[str] = []
    for role_key in plan.roles:
        try:
            text, review = produce(role_key, task, llm, "\n\n".join(context_parts))
        except Exception as exc:  # one failing specialist must not hide the others
            log.exception("specialist %s failed", role_key)
            record.artifacts.append(ArtifactRecord(role_key, None, None, error=repr(exc)))
            append_log(
                {
                    "event": "specialist_error",
                    "run_id": run_id,
                    "role": role_key,
                    "error": repr(exc),
                },
                log_file,
            )
        else:
            path = out / f"{role_key}.md"
            path.write_text(text, encoding="utf-8")
            review_dict = asdict(review) | {"verdict": review.verdict}
            record.artifacts.append(ArtifactRecord(role_key, path.name, review_dict))
            context_parts.append(f"[{get_role(role_key).title}]\n{_excerpt(text)}")
            append_log(
                {
                    "event": "artifact",
                    "run_id": run_id,
                    "role": role_key,
                    "verdict": review.verdict,
                    "issues": review.issues,
                },
                log_file,
            )
        write_manifest(out, asdict(record))

    record.status = "pending"
    write_manifest(out, asdict(record))
    clear_lock(out)
    append_log(
        {
            "event": "run_end",
            "run_id": run_id,
            "governance_clean": record.all_approved_by_governance,
            "errors": sum(1 for a in record.artifacts if a.error),
        },
        log_file,
    )
    return record
